"""Tests for test run persistence."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from goose.testing.api.persistence import LatestIndex, StoredRun, TestRunHistory, TestRunStore
from goose.testing.api.schema import TestResultModel


def _make_result(name: str, passed: bool = True) -> TestResultModel:
    """Create a minimal TestResultModel for testing."""
    return TestResultModel(
        qualified_name=name,
        name=name.split(".")[-1],
        module=".".join(name.split(".")[:-1]) or "test_module",
        query="test query",
        expectations=["expect something"],
        passed=passed,
        duration=1.0,
    )


class TestStoredRun:
    def test_create_stored_run(self) -> None:
        result = _make_result("test_module.test_one")
        run = StoredRun(
            id="job-1",
            timestamp=datetime.now(timezone.utc),
            result=result,
        )

        assert run.id == "job-1"
        assert run.result.qualified_name == "test_module.test_one"


class TestTestRunHistory:
    def test_empty_history(self) -> None:
        history = TestRunHistory()
        assert history.runs == []

    def test_history_with_runs(self) -> None:
        result = _make_result("test_module.test_one")
        run = StoredRun(
            id="job-1",
            timestamp=datetime.now(timezone.utc),
            result=result,
        )
        history = TestRunHistory(runs=[run])

        assert len(history.runs) == 1
        assert history.runs[0].id == "job-1"


class TestLatestIndex:
    def test_empty_index(self) -> None:
        index = LatestIndex()
        assert index.latest == {}

    def test_index_with_runs(self) -> None:
        result = _make_result("test_module.test_one")
        run = StoredRun(
            id="job-1",
            timestamp=datetime.now(timezone.utc),
            result=result,
        )
        index = LatestIndex(latest={"test_module.test_one": run})

        assert "test_module.test_one" in index.latest
        assert index.latest["test_module.test_one"].id == "job-1"


class TestTestRunStore:
    def test_init_creates_empty_history(self, tmp_path: Path) -> None:
        store = TestRunStore(tmp_path)

        assert store.run_count() == 0
        assert store.get_latest_results() == {}

    def test_add_run_persists_to_files(self, tmp_path: Path) -> None:
        store = TestRunStore(tmp_path)
        result = _make_result("test_module.test_one")

        store.add_run("job-1", result)

        assert store.run_count() == 1

        # Verify index file
        assert (tmp_path / "latest.json").exists()
        with open(tmp_path / "latest.json") as f:
            data = json.load(f)
        assert "test_module.test_one" in data["latest"]

        # Verify history file
        assert (tmp_path / "history" / "test_module.test_one.json").exists()

    def test_add_multiple_runs(self, tmp_path: Path) -> None:
        store = TestRunStore(tmp_path)
        result1 = _make_result("test_module.test_one")
        result2 = _make_result("test_module.test_two")

        store.add_run("job-1", result1)
        store.add_run("job-2", result2)

        assert store.run_count() == 2

        # Should have two separate history files
        assert (tmp_path / "history" / "test_module.test_one.json").exists()
        assert (tmp_path / "history" / "test_module.test_two.json").exists()

    def test_get_latest_results_returns_most_recent(self, tmp_path: Path) -> None:
        store = TestRunStore(tmp_path)

        # Add two runs for the same test
        result1 = _make_result("test_module.test_one", passed=False)
        result2 = _make_result("test_module.test_one", passed=True)

        store.add_run("job-1", result1)
        store.add_run("job-2", result2)

        latest = store.get_latest_results()

        assert len(latest) == 1
        assert latest["test_module.test_one"].passed is True

    def test_get_latest_results_multiple_tests(self, tmp_path: Path) -> None:
        store = TestRunStore(tmp_path)

        store.add_run("job-1", _make_result("test_module.test_one"))
        store.add_run("job-2", _make_result("test_module.test_two"))

        latest = store.get_latest_results()

        assert len(latest) == 2
        assert "test_module.test_one" in latest
        assert "test_module.test_two" in latest

    def test_get_all_runs_returns_chronological_order(self, tmp_path: Path) -> None:
        store = TestRunStore(tmp_path)

        store.add_run("job-1", _make_result("test_module.test_one"))
        store.add_run("job-2", _make_result("test_module.test_two"))
        store.add_run("job-3", _make_result("test_module.test_three"))

        runs = store.get_all_runs()

        assert len(runs) == 3
        assert runs[0].id == "job-1"
        assert runs[1].id == "job-2"
        assert runs[2].id == "job-3"

    def test_get_runs_for_test_filters_correctly(self, tmp_path: Path) -> None:
        store = TestRunStore(tmp_path)

        store.add_run("job-1", _make_result("test_module.test_one"))
        store.add_run("job-2", _make_result("test_module.test_two"))
        store.add_run("job-3", _make_result("test_module.test_one"))

        runs = store.get_runs_for_test("test_module.test_one")

        assert len(runs) == 2
        assert all(r.result.qualified_name == "test_module.test_one" for r in runs)

    def test_clear_removes_all_data(self, tmp_path: Path) -> None:
        store = TestRunStore(tmp_path)

        store.add_run("job-1", _make_result("test_module.test_one"))
        store.add_run("job-2", _make_result("test_module.test_two"))
        assert store.run_count() == 2

        store.clear()

        assert store.run_count() == 0
        assert store.get_latest_results() == {}
        assert not (tmp_path / "latest.json").exists()
        assert not (tmp_path / "history").exists()

    def test_load_persisted_data_on_init(self, tmp_path: Path) -> None:
        # Create a store and add data
        store1 = TestRunStore(tmp_path)
        store1.add_run("job-1", _make_result("test_module.test_one"))
        store1.add_run("job-2", _make_result("test_module.test_two"))

        # Create a new store instance - should load persisted data
        store2 = TestRunStore(tmp_path)

        assert store2.run_count() == 2
        latest = store2.get_latest_results()
        assert "test_module.test_one" in latest
        assert "test_module.test_two" in latest

    def test_handles_corrupted_index_file(self, tmp_path: Path) -> None:
        # Write corrupted JSON to index
        (tmp_path / "latest.json").write_text("not valid json {{{")

        # Should not raise, returns empty
        store = TestRunStore(tmp_path)
        assert store.get_latest_results() == {}

    def test_handles_invalid_index_schema(self, tmp_path: Path) -> None:
        # Write valid JSON but invalid schema
        (tmp_path / "latest.json").write_text('{"latest": "not a dict"}')

        # Should not raise, returns empty
        store = TestRunStore(tmp_path)
        assert store.get_latest_results() == {}

    def test_handles_corrupted_history_file(self, tmp_path: Path) -> None:
        store = TestRunStore(tmp_path)
        store.add_run("job-1", _make_result("test_module.test_one"))

        # Corrupt the history file
        history_file = tmp_path / "history" / "test_module.test_one.json"
        history_file.write_text("corrupted {{{")

        # Should return empty runs for that test
        runs = store.get_runs_for_test("test_module.test_one")
        assert runs == []

    def test_creates_data_directory_if_missing(self, tmp_path: Path) -> None:
        nested_path = tmp_path / "nested" / "data" / "dir"
        store = TestRunStore(nested_path)

        store.add_run("job-1", _make_result("test_module.test_one"))

        assert nested_path.exists()
        assert (nested_path / "latest.json").exists()
        assert (nested_path / "history").exists()

    def test_history_accumulates_for_same_test(self, tmp_path: Path) -> None:
        store = TestRunStore(tmp_path)

        # Add multiple runs for the same test
        store.add_run("job-1", _make_result("test_module.test_one", passed=False))
        store.add_run("job-2", _make_result("test_module.test_one", passed=True))
        store.add_run("job-3", _make_result("test_module.test_one", passed=False))

        # History should have all runs
        runs = store.get_runs_for_test("test_module.test_one")
        assert len(runs) == 3
        assert runs[0].id == "job-1"
        assert runs[1].id == "job-2"
        assert runs[2].id == "job-3"

        # Latest should only have the most recent
        latest = store.get_latest_results()
        assert len(latest) == 1

    def test_clear_test_history_removes_single_test(self, tmp_path: Path) -> None:
        store = TestRunStore(tmp_path)

        store.add_run("job-1", _make_result("test_module.test_one"))
        store.add_run("job-2", _make_result("test_module.test_two"))
        store.add_run("job-3", _make_result("test_module.test_one"))

        store.clear_test_history("test_module.test_one")

        # test_one should be gone
        assert store.get_runs_for_test("test_module.test_one") == []
        assert "test_module.test_one" not in store.get_latest_results()

        # test_two should still exist
        assert len(store.get_runs_for_test("test_module.test_two")) == 1
        assert "test_module.test_two" in store.get_latest_results()

    def test_delete_run_at_index_removes_specific_run(self, tmp_path: Path) -> None:
        store = TestRunStore(tmp_path)

        store.add_run("job-1", _make_result("test_module.test_one", passed=False))
        store.add_run("job-2", _make_result("test_module.test_one", passed=True))
        store.add_run("job-3", _make_result("test_module.test_one", passed=False))

        # Delete the middle run (index 1)
        success = store.delete_run_at_index("test_module.test_one", 1)

        assert success
        runs = store.get_runs_for_test("test_module.test_one")
        assert len(runs) == 2
        assert runs[0].id == "job-1"
        assert runs[1].id == "job-3"

    def test_delete_run_at_index_updates_latest_when_deleting_newest(self, tmp_path: Path) -> None:
        store = TestRunStore(tmp_path)

        store.add_run("job-1", _make_result("test_module.test_one", passed=False))
        store.add_run("job-2", _make_result("test_module.test_one", passed=True))

        # Delete the latest run (index 1)
        store.delete_run_at_index("test_module.test_one", 1)

        # Latest should now be job-1
        latest = store.get_latest_results()
        assert latest["test_module.test_one"].passed is False

    def test_delete_run_at_index_clears_when_last_run_deleted(self, tmp_path: Path) -> None:
        store = TestRunStore(tmp_path)

        store.add_run("job-1", _make_result("test_module.test_one"))

        # Delete the only run
        success = store.delete_run_at_index("test_module.test_one", 0)

        assert success
        assert store.get_runs_for_test("test_module.test_one") == []
        assert "test_module.test_one" not in store.get_latest_results()

    def test_delete_run_at_index_returns_false_for_invalid_index(self, tmp_path: Path) -> None:
        store = TestRunStore(tmp_path)

        store.add_run("job-1", _make_result("test_module.test_one"))

        assert store.delete_run_at_index("test_module.test_one", 5) is False
        assert store.delete_run_at_index("test_module.test_one", -1) is False
        assert store.delete_run_at_index("test_module.nonexistent", 0) is False
