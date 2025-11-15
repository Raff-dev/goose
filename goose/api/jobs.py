"""In-memory job orchestration for the Goose FastAPI service."""

from __future__ import annotations

import copy
import queue
import threading
import traceback
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from goose.testing.discovery import load_test_definition
from goose.testing.runner import list_tests, run_single_test
from goose.testing.types import TestDefinition, TestResult


class JobStatus(str, Enum):
    """Enumerates the lifecycle states for an execution job."""

    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class JobMode(str, Enum):
    """Indicates how a job selects tests for execution."""

    ALL = "all"
    SELECTIVE = "selective"


@dataclass(slots=True, frozen=True)
class TestTarget:
    """Lightweight identifier for a test function to execute."""

    module: str
    name: str

    @property
    def qualified_name(self) -> str:
        """Return the fully-qualified dotted name for the test."""

        return f"{self.module}.{self.name}"

    @classmethod
    def from_definition(cls, definition: TestDefinition) -> TestTarget:
        """Build a target from a discovered test definition."""

        return cls(module=definition.module, name=definition.name)


@dataclass(slots=True)
# Dataclass fields intentionally capture the job state; migrations and
# runtime orchestration require several attributes. Disable the pylint
# warning here as the structure is deliberate.
# pylint: disable=too-many-instance-attributes
class Job:
    """Represents the state of a queued or executing test run."""

    id: str
    status: JobStatus
    mode: JobMode
    targets: list[TestTarget]
    created_at: datetime
    updated_at: datetime
    results: list[TestResult] = field(default_factory=list)
    error: str | None = None
    test_statuses: dict[str, str] = field(default_factory=dict)


class UnknownTestError(ValueError):
    """Raised when a requested test cannot be located."""


class JobStore:
    """Thread-safe storage for job metadata."""

    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}
        self._lock = threading.Lock()

    def create_job(self, *, targets: list[TestTarget], mode: JobMode) -> Job:
        """Create and persist a new job in the queued state."""

        job_id = str(uuid.uuid4())
        now = datetime.utcnow()
        job = Job(
            id=job_id,
            status=JobStatus.QUEUED,
            mode=mode,
            targets=list(targets),
            created_at=now,
            updated_at=now,
            test_statuses={target.qualified_name: "queued" for target in targets},
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
            job.updated_at = datetime.utcnow()
            job.results.clear()
            job.error = None
            # Set all to queued, then first to running
            job.test_statuses = {target.qualified_name: "queued" for target in job.targets}
            if job.targets:
                job.test_statuses[job.targets[0].qualified_name] = "running"
            return copy.deepcopy(job)

    def mark_succeeded(self, job_id: str, results: list[TestResult]) -> Job | None:
        """Persist successful completion details for a job."""

        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return None
            job.status = JobStatus.SUCCEEDED
            job.updated_at = datetime.utcnow()
            job.results = list(results)
            job.error = None
            job.test_statuses = {
                result.definition.qualified_name: "passed" if result.passed else "failed" for result in results
            }
            return copy.deepcopy(job)

    def mark_failed(self, job_id: str, message: str) -> Job | None:
        """Persist a failure message for a job.

        This is used when the background worker encounters an unexpected
        exception while executing a job. The job-level status is set to
        FAILED, results are cleared and all per-test statuses are marked
        as failed to reflect the terminal state.
        """

        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return None
            job.status = JobStatus.FAILED
            job.updated_at = datetime.utcnow()
            job.error = message
            job.results.clear()
            job.test_statuses = {target.qualified_name: "failed" for target in job.targets}
            return copy.deepcopy(job)

    def update_test_status(self, job_id: str, test_name: str, status: str) -> Job | None:
        """Update the status of a specific test in a job."""

        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return None
            job.test_statuses[test_name] = status
            job.updated_at = datetime.utcnow()
            return copy.deepcopy(job)


class ExecutionService:
    """Coordinates job submission and sequential background execution."""

    def __init__(self) -> None:
        self._store = JobStore()
        self._queue: queue.Queue[str] = queue.Queue()
        self._worker = threading.Thread(target=self._worker_loop, name="goose-api-worker", daemon=True)
        self._worker.start()

    def submit(self, tests: list[str] | None) -> Job:
        """Queue a new job for execution."""

        targets, mode = self._resolve_targets(tests)
        job = self._store.create_job(targets=targets, mode=mode)
        self._queue.put(job.id)
        return job

    def get_job(self, job_id: str) -> Job | None:
        """Return a snapshot of the requested job."""

        return self._store.get_job(job_id)

    def list_jobs(self) -> list[Job]:
        """Return snapshots for all tracked jobs."""

        return self._store.list_jobs()

    def _resolve_targets(self, requested: list[str] | None) -> tuple[list[TestTarget], JobMode]:
        """Resolve requested test names into executable targets."""
        definitions = list_tests()
        if not definitions:
            raise UnknownTestError("No Goose tests discovered to execute.")

        if requested is None:
            targets = [TestTarget.from_definition(definition) for definition in definitions]
            return targets, JobMode.ALL

        if not requested:
            raise UnknownTestError("At least one test must be specified when using targeted execution.")

        known: dict[str, TestDefinition] = {definition.qualified_name: definition for definition in definitions}
        seen: set[str] = set()
        resolved_targets: list[TestTarget] = []
        for qualified_name in requested:
            if qualified_name in seen:
                continue
            definition = known.get(qualified_name)
            if definition is None:
                raise UnknownTestError(f"Unknown test requested: {qualified_name}")
            resolved_targets.append(TestTarget.from_definition(definition))
            seen.add(qualified_name)

        if not resolved_targets:
            raise UnknownTestError("No valid tests resolved from the provided identifiers.")

        return resolved_targets, JobMode.SELECTIVE

    def _worker_loop(self) -> None:
        """Process queued jobs sequentially in a single background thread."""

        while True:
            job_id = self._queue.get()
            job = self._store.mark_running(job_id)
            if job is None:
                continue

            try:
                results = self._execute_job(job)
            except Exception:  # pylint: disable=broad-exception-caught
                message = traceback.format_exc()
                self._store.mark_failed(job_id, message)
                continue

            self._store.mark_succeeded(job_id, results)

    def _execute_job(self, job: Job) -> list[TestResult]:
        """Execute tests for the provided job snapshot."""

        # Use the top-level imported ``list_tests`` to discover tests.
        # (Avoid re-importing here to keep imports at module level.)

        results: list[TestResult] = []

        if job.mode is JobMode.ALL:
            definitions = list_tests()
            for definition in definitions:
                target_name = definition.qualified_name
                self._store.update_test_status(job.id, target_name, "running")
                result = run_single_test(definition)
                results.append(result)
                status = "passed" if result.passed else "failed"
                self._store.update_test_status(job.id, target_name, status)
            return results

        for target in job.targets:
            # Update status to running before executing
            self._store.update_test_status(job.id, target.qualified_name, "running")
            definition = load_test_definition(target.module, target.name)
            result = run_single_test(definition)
            results.append(result)
            # Update status to passed/failed after executing
            status = "passed" if result.passed else "failed"
            self._store.update_test_status(job.id, target.qualified_name, status)
        return results


__all__ = [
    "ExecutionService",
    "Job",
    "JobMode",
    "JobStatus",
    "TestTarget",
    "UnknownTestError",
]
