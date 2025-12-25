"""File-based persistence for test run history.

Uses a hybrid storage approach:
- latest.json: Index file with most recent result per test (fast grid loading)
- history/<test_name>.json: Per-test history files (lazy loaded on demand)

This provides fast startup (only reads latest.json) and efficient writes
(only updates one test's history file + index).
"""

from __future__ import annotations

import json
import re
import shutil
import threading
from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel, Field

from goose.testing.api.schema import TestResultModel


class StoredRun(BaseModel):
    """A single persisted test run with metadata."""

    id: str
    timestamp: datetime
    result: TestResultModel


class TestRunHistory(BaseModel):
    """Container for persisted test runs (used for per-test history files)."""

    __test__ = False

    runs: list[StoredRun] = Field(default_factory=list)


class LatestIndex(BaseModel):
    """Index of latest results per test for fast grid loading."""

    __test__ = False

    latest: dict[str, StoredRun] = Field(default_factory=dict)


def _sanitize_filename(qualified_name: str) -> str:
    """Convert a qualified test name to a safe filename.

    Args:
        qualified_name: The fully qualified test name (e.g., "module.test_func").

    Returns:
        A filesystem-safe filename with .json extension.
    """
    safe_name = re.sub(r"[^\w\-.]", "_", qualified_name)
    return f"{safe_name}.json"


class TestRunStore:
    """Thread-safe file-backed storage for test run history.

    Uses a hybrid approach with an index file for fast loading and
    per-test history files for efficient writes.

    Storage layout:
        data/
            latest.json              # Index: latest result per test
            history/
                module_test_one.json # Full history for this test
                module_test_two.json
    """

    __test__ = False

    def __init__(self, data_path: Path) -> None:
        """Initialize the store with the given data directory.

        Args:
            data_path: Directory where test data will be stored.
        """
        self._data_path = data_path
        self._index_path = data_path / "latest.json"
        self._history_path = data_path / "history"
        self._lock = threading.Lock()
        self._index: LatestIndex = self._load_index()

    def _load_index(self) -> LatestIndex:
        """Load the latest index from disk."""
        if not self._index_path.exists():
            return LatestIndex()

        try:
            with open(self._index_path, encoding="utf-8") as f:
                data = json.load(f)
            return LatestIndex.model_validate(data)
        except (json.JSONDecodeError, ValueError):
            return LatestIndex()

    def _save_index(self) -> None:
        """Persist the latest index to disk."""
        self._data_path.mkdir(parents=True, exist_ok=True)
        with open(self._index_path, "w", encoding="utf-8") as f:
            json.dump(self._index.model_dump(mode="json"), f, indent=2, default=str)

    def _get_history_file(self, qualified_name: str) -> Path:
        """Get the path to a test's history file."""
        return self._history_path / _sanitize_filename(qualified_name)

    def _load_test_history(self, qualified_name: str) -> TestRunHistory:
        """Load history for a specific test."""
        history_file = self._get_history_file(qualified_name)
        if not history_file.exists():
            return TestRunHistory()

        try:
            with open(history_file, encoding="utf-8") as f:
                data = json.load(f)
            return TestRunHistory.model_validate(data)
        except (json.JSONDecodeError, ValueError):
            return TestRunHistory()

    def _save_test_history(self, qualified_name: str, history: TestRunHistory) -> None:
        """Persist history for a specific test."""
        self._history_path.mkdir(parents=True, exist_ok=True)
        history_file = self._get_history_file(qualified_name)
        with open(history_file, "w", encoding="utf-8") as f:
            json.dump(history.model_dump(mode="json"), f, indent=2, default=str)

    def add_run(self, job_id: str, result: TestResultModel) -> None:
        """Add a new test run to the history.

        Updates both the latest index and the test's history file.

        Args:
            job_id: The job ID that produced this result.
            result: The test result to persist.
        """
        stored_run = StoredRun(
            id=job_id,
            timestamp=datetime.now(timezone.utc),
            result=result,
        )
        qualified_name = result.qualified_name

        with self._lock:
            # Update the index
            self._index.latest[qualified_name] = stored_run
            self._save_index()

            # Append to test's history file
            history = self._load_test_history(qualified_name)
            history.runs.append(stored_run)
            self._save_test_history(qualified_name, history)

    def get_latest_results(self) -> dict[str, TestResultModel]:
        """Return the most recent result for each test.

        This is fast - only reads the index file.

        Returns:
            A mapping from qualified test name to its latest result.
        """
        with self._lock:
            return {name: stored.result for name, stored in self._index.latest.items()}

    def get_all_runs(self) -> list[StoredRun]:
        """Return all stored runs in chronological order.

        Note: This reads all history files. Use sparingly.

        Returns:
            List of all stored runs, oldest first.
        """
        all_runs: list[StoredRun] = []

        with self._lock:
            if not self._history_path.exists():
                return []

            for history_file in self._history_path.glob("*.json"):
                try:
                    with open(history_file, encoding="utf-8") as f:
                        data = json.load(f)
                    history = TestRunHistory.model_validate(data)
                    all_runs.extend(history.runs)
                except (json.JSONDecodeError, ValueError):
                    continue

        all_runs.sort(key=lambda r: r.timestamp)
        return all_runs

    def get_runs_for_test(self, qualified_name: str) -> list[StoredRun]:
        """Return all runs for a specific test.

        This is efficient - only reads one history file.

        Args:
            qualified_name: The fully qualified test name.

        Returns:
            List of runs for the test, oldest first.
        """
        with self._lock:
            history = self._load_test_history(qualified_name)

        runs = list(history.runs)
        runs.sort(key=lambda r: r.timestamp)
        return runs

    def clear(self) -> None:
        """Delete all stored test run history."""
        with self._lock:
            self._index = LatestIndex()

            # Delete index file
            if self._index_path.exists():
                self._index_path.unlink()

            # Delete entire history directory
            if self._history_path.exists():
                shutil.rmtree(self._history_path)

    def clear_test_history(self, qualified_name: str) -> None:
        """Delete all stored runs for a specific test.

        Args:
            qualified_name: The fully qualified test name.
        """
        with self._lock:
            # Remove from index
            if qualified_name in self._index.latest:
                del self._index.latest[qualified_name]
                self._save_index()

            # Delete the history file
            history_file = self._get_history_file(qualified_name)
            if history_file.exists():
                history_file.unlink()

    def delete_run_at_index(self, qualified_name: str, index: int) -> bool:
        """Delete a specific run by index (0-based, oldest first).

        Args:
            qualified_name: The fully qualified test name.
            index: The 0-based index of the run to delete.

        Returns:
            True if the run was deleted, False if index was out of range.
        """
        with self._lock:
            history = self._load_test_history(qualified_name)
            runs = list(history.runs)
            runs.sort(key=lambda r: r.timestamp)

            if index < 0 or index >= len(runs):
                return False

            # Remove the run
            deleted_run = runs.pop(index)
            history.runs = runs

            if not runs:
                # No runs left - clear test history entirely
                if qualified_name in self._index.latest:
                    del self._index.latest[qualified_name]
                    self._save_index()
                history_file = self._get_history_file(qualified_name)
                if history_file.exists():
                    history_file.unlink()
            else:
                # Save updated history
                self._save_test_history(qualified_name, history)

                # Update index if we deleted the latest run
                if self._index.latest.get(qualified_name) == deleted_run:
                    # Find new latest
                    new_latest = max(runs, key=lambda r: r.timestamp)
                    self._index.latest[qualified_name] = new_latest
                    self._save_index()

            return True

    def run_count(self) -> int:
        """Return the total number of stored runs.

        Note: This counts runs across all history files.
        """
        count = 0

        with self._lock:
            if not self._history_path.exists():
                return 0

            for history_file in self._history_path.glob("*.json"):
                try:
                    with open(history_file, encoding="utf-8") as f:
                        data = json.load(f)
                    history = TestRunHistory.model_validate(data)
                    count += len(history.runs)
                except (json.JSONDecodeError, ValueError):
                    continue

        return count


__all__ = ["LatestIndex", "StoredRun", "TestRunHistory", "TestRunStore"]
