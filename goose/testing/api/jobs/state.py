"""Job metadata and storage primitives for Goose API."""

from __future__ import annotations

import copy
import threading
import uuid
from datetime import datetime, timezone

from goose.testing.api.jobs.enums import JobStatus, TestStatus
from goose.testing.api.jobs.models import Job
from goose.testing.models.tests import TestDefinition, TestResult


class JobStore:
    """Thread-safe storage for job metadata."""

    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}
        self._lock = threading.Lock()

    def create_job(self, *, targets: list[TestDefinition]) -> Job:
        """Create and persist a new job in the queued state."""

        job_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        job = Job(
            id=job_id,
            status=JobStatus.QUEUED,
            targets=list(targets),
            created_at=now,
            updated_at=now,
            test_statuses={target.qualified_name: TestStatus.QUEUED for target in targets},
        )
        with self._lock:
            self._jobs[job_id] = job
        return copy.deepcopy(job)

    def get_job(self, job_id: str) -> Job | None:
        """Return a copy of a stored job by identifier."""

        with self._lock:
            job = self._jobs.get(job_id)
            return copy.deepcopy(job) if job is not None else None

    def list_jobs(self) -> list[Job]:
        """Return all known jobs sorted by creation time descending."""

        with self._lock:
            jobs = list(self._jobs.values())
        jobs.sort(key=lambda item: item.created_at, reverse=True)
        return [copy.deepcopy(item) for item in jobs]

    def mark_running(self, job_id: str) -> Job | None:
        """Transition a job to the running state."""

        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return None
            job.status = JobStatus.RUNNING
            job.updated_at = datetime.now(timezone.utc)
            job.results.clear()
            job.error = None
            job.test_statuses = {target.qualified_name: TestStatus.QUEUED for target in job.targets}
            if job.targets:
                job.test_statuses[job.targets[0].qualified_name] = TestStatus.RUNNING
            return copy.deepcopy(job)

    def mark_succeeded(self, job_id: str, results: list[TestResult]) -> Job | None:
        """Persist successful completion details for a job."""

        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return None
            job.status = JobStatus.SUCCEEDED
            job.updated_at = datetime.now(timezone.utc)
            job.results = list(results)
            job.error = None
            if results:
                job.test_statuses = {
                    result.definition.qualified_name: (TestStatus.PASSED if result.passed else TestStatus.FAILED)
                    for result in results
                }
            else:
                job.test_statuses = {target.qualified_name: TestStatus.PASSED for target in job.targets}
            return copy.deepcopy(job)

    def mark_failed(self, job_id: str, message: str) -> Job | None:
        """Persist a failure message for a job."""

        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return None
            job.status = JobStatus.FAILED
            job.updated_at = datetime.now(timezone.utc)
            job.error = message
            job.results.clear()
            job.test_statuses = {target.qualified_name: TestStatus.FAILED for target in job.targets}
            return copy.deepcopy(job)

    def update_test_status(self, job_id: str, test_name: str, status: TestStatus) -> Job | None:
        """Update the status of a specific test in a job."""

        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return None
            job.test_statuses[test_name] = status
            job.updated_at = datetime.now(timezone.utc)
            return copy.deepcopy(job)

    def add_test_result(self, job_id: str, result: TestResult) -> Job | None:
        """Add a completed test result to a job and update its status."""

        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return None
            job.results.append(result)
            status = TestStatus.PASSED if result.passed else TestStatus.FAILED
            job.test_statuses[result.definition.qualified_name] = status
            job.updated_at = datetime.now(timezone.utc)
            return copy.deepcopy(job)


__all__ = ["JobStore"]
