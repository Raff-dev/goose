"""In-memory queue that schedules and runs Goose jobs."""

from __future__ import annotations

import queue
import threading
import traceback
from collections.abc import Callable

from goose.testing.api.jobs.enums import TestStatus
from goose.testing.api.jobs.models import Job
from goose.testing.api.jobs.state import JobStore
from goose.testing.models.tests import TestDefinition, TestResult
from goose.testing.runner import execute_test


class JobQueue:
    """Dispatch requested tests to the runner and track their progress."""

    def __init__(
        self,
        *,
        on_job_update: Callable[[Job], None] | None = None,
        on_result_added: Callable[[str, TestResult], None] | None = None,
        job_store: JobStore = JobStore(),
    ) -> None:
        self.job_store = job_store
        self._queue: queue.Queue[tuple[str, list[TestDefinition]]] = queue.Queue()
        self._on_job_update = on_job_update
        self._on_result_added = on_result_added
        threading.Thread(target=self._worker_loop, daemon=True, name="GooseJobWorker").start()

    def enqueue(self, targets: list[TestDefinition]) -> Job:
        """Create a job and place it on the execution queue."""

        job = self.job_store.create_job(targets=targets)
        self._queue.put((job.id, targets))
        self._notify(job)
        return job

    def _execute_targets(self, job_id: str, targets: list[TestDefinition]) -> list[TestResult]:
        """Run the provided tests sequentially, updating per-test status."""

        results: list[TestResult] = []
        for definition in targets:
            qualified_name = definition.qualified_name
            running_snapshot = self.job_store.update_test_status(job_id, qualified_name, TestStatus.RUNNING)
            self._notify(running_snapshot)

            result = execute_test(definition)
            results.append(result)
            # Add result to job immediately so frontend can show details
            snapshot = self.job_store.add_test_result(job_id, result)
            self._notify(snapshot)

            # Notify that a result was added (for persistence)
            if self._on_result_added is not None:
                self._on_result_added(job_id, result)

        return results

    def list_jobs(self) -> list[Job]:
        """Return a snapshot of all known jobs."""

        return self.job_store.list_jobs()

    def get_job(self, job_id: str) -> Job | None:
        """Return a single job by identifier."""

        return self.job_store.get_job(job_id)

    def _notify(self, job: Job | None) -> None:
        """Invoke the configured callback with the latest job snapshot."""

        if job is None or self._on_job_update is None:
            return
        self._on_job_update(job)

    def _run_job(self, job_id: str, targets: list[TestDefinition]) -> Job | None:
        """Execute a queued job and update observers."""

        job = self.job_store.mark_running(job_id)
        if job is None:
            return None
        self._notify(job)

        try:
            results = self._execute_targets(job_id, targets)
            final_job = self.job_store.mark_succeeded(job_id, results)
            self._notify(final_job)
            return final_job
        except Exception as exc:  # pylint: disable=broad-except
            error_message = "\n".join(traceback.format_exception(exc))
            failed_job = self.job_store.mark_failed(job_id, error_message)
            self._notify(failed_job)
            return failed_job

    def _worker_loop(self) -> None:
        """Background worker that processes the job queue sequentially."""

        while True:
            job_id, targets = self._queue.get()
            try:
                self._run_job(job_id, targets)
            finally:
                self._queue.task_done()


__all__ = ["JobQueue"]
