"""Background job execution service for Goose API."""

from __future__ import annotations

import queue
import traceback
from collections.abc import Callable

from goose.api.jobs.enums import JobMode
from goose.api.jobs.models import Job, TestTarget
from goose.api.jobs.state import JobStore
from goose.testing.discovery import load_test_definition
from goose.testing.runner import list_tests, run_single_test
from goose.testing.types import TestResult


class UnknownTestError(ValueError):
    """Raised when a requested test cannot be located."""


class ExecutionService:
    """Dispatches requested tests to the runner and tracks their progress."""

    def __init__(
        self,
        *,
        on_job_update: Callable[[Job], None] | None = None,
        job_store: JobStore | None = None,
    ) -> None:
        self.job_store = job_store or JobStore()
        self._queue: queue.Queue[tuple[str, list[TestTarget]]] = queue.Queue()
        self._on_job_update = on_job_update

    def submit(self, tests: list[str] | None = None) -> Job:
        """Resolve targets for ``tests`` and execute them immediately."""

        mode = JobMode.ALL if not tests else JobMode.SELECTIVE
        targets = self.resolve_targets(mode, tests)
        job = self.enqueue(targets=targets)
        processed = self.process_next()
        return processed or job

    def enqueue(self, targets: list[TestTarget]) -> Job:
        """Create a job and place it on the execution queue."""

        job = self.job_store.create_job(targets=targets)
        self._queue.put((job.id, targets))
        self._notify(job)
        return job

    def process_next(self) -> Job | None:
        """Pop the next job from the queue and execute it synchronously."""

        try:
            job_id, targets = self._queue.get_nowait()
        except queue.Empty:
            return None

        job = self.job_store.mark_running(job_id)
        if job is None:
            return None
        self._notify(job)

        try:
            results = self._execute_targets(job_id, targets)
            final_job = self.job_store.mark_succeeded(job_id, results)
            self._notify(final_job)
            return final_job
        except Exception as exc:  # pylint: disable=broad-exception-caught
            error_message = "\n".join(traceback.format_exception(exc))
            failed_job = self.job_store.mark_failed(job_id, error_message)
            self._notify(failed_job)
            return failed_job
        finally:
            self._queue.task_done()

    def _execute_targets(self, job_id: str, targets: list[TestTarget]) -> list[TestResult]:
        """Run the provided tests sequentially, updating per-test status."""

        results: list[TestResult] = []
        for index, target in enumerate(targets):
            qualified_name = target.qualified_name
            running_snapshot = self.job_store.update_test_status(job_id, qualified_name, "running")
            self._notify(running_snapshot)
            definition = load_test_definition(target.module, target.name)
            result = run_single_test(definition)
            results.append(result)
            status = "passed" if result.passed else "failed"
            snapshot = self.job_store.update_test_status(job_id, qualified_name, status)
            self._notify(snapshot)
            if index + 1 < len(targets):
                next_target = targets[index + 1]
                pending_snapshot = self.job_store.update_test_status(job_id, next_target.qualified_name, "running")
                self._notify(pending_snapshot)
        return results

    def list_jobs(self) -> list[Job]:
        """Return a snapshot of all known jobs."""

        return self.job_store.list_jobs()

    def get_job(self, job_id: str) -> Job | None:
        """Return a single job by identifier."""

        return self.job_store.get_job(job_id)

    def requeue_job(self, job_id: str) -> Job | None:
        """Duplicate an existing job request and enqueue it again."""

        job = self.job_store.get_job(job_id)
        if job is None:
            return None

        new_job = self.job_store.create_job(targets=job.targets)
        self._queue.put((new_job.id, new_job.targets))
        self._notify(new_job)
        return new_job

    def resolve_all_targets(self) -> list[TestTarget]:
        """Discover every available test target."""

        tests = list_tests()
        return [TestTarget.from_definition(test) for test in tests]

    def resolve_specific_targets(self, requested: list[str]) -> list[TestTarget]:
        """Resolve explicit dotted test names to concrete targets."""

        resolved: list[TestTarget] = []
        for qualified_name in requested:
            try:
                target = TestTarget.from_qualified_name(qualified_name)
            except ValueError as exc:  # pragma: no cover - defensive guard
                raise UnknownTestError(f"Test name must be module-qualified: {qualified_name}") from exc
            resolved.append(self._resolve_target(target))
        return resolved

    def resolve_targets(self, mode: JobMode, requested: list[str] | None = None) -> list[TestTarget]:
        """Choose target resolution strategy based on job mode."""

        if mode == JobMode.ALL:
            return self.resolve_all_targets()
        if not requested:
            raise UnknownTestError("No test names provided for selective execution.")
        return self.resolve_specific_targets(requested)

    def _resolve_target(self, target: TestTarget) -> TestTarget:
        """Resolve a single test target to ensure it exists."""

        try:
            definition = load_test_definition(target.module, target.name)
        except (AttributeError, ModuleNotFoundError, ValueError) as exc:
            raise UnknownTestError(f"Test not found: {target.qualified_name}") from exc
        return TestTarget.from_definition(definition)

    def _notify(self, job: Job | None) -> None:
        """Invoke the configured callback with the latest job snapshot."""

        if job is None or self._on_job_update is None:
            return
        self._on_job_update(job)


__all__ = [
    "ExecutionService",
    "UnknownTestError",
]
