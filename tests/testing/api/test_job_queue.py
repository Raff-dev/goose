from __future__ import annotations

from collections import deque

from goose.testing.api.jobs.enums import JobStatus, TestStatus
from goose.testing.api.jobs.job_queue import JobQueue
from goose.testing.api.jobs.state import JobStore
from goose.testing.models.tests import TestDefinition, TestResult


def _make_definition(name: str = "test_case") -> TestDefinition:
    def _case() -> None:  # pragma: no cover - helper only
        return None

    return TestDefinition(module="pkg.tests", name=name, func=_case)


def test_job_queue_runs_targets_to_completion(monkeypatch) -> None:
    store = JobStore()
    updates: deque[JobStatus] = deque()

    def fake_execute(definition: TestDefinition) -> TestResult:
        return TestResult(definition=definition, duration=0.05, test_case=None, exception=None)

    monkeypatch.setattr("goose.testing.api.jobs.job_queue.execute_test", fake_execute)

    queue = JobQueue(on_job_update=lambda job: updates.append(job.status), job_store=store)
    definition = _make_definition()

    job = queue.enqueue([definition])
    queue._queue.join()  # type: ignore[attr-defined]

    snapshot = store.get_job(job.id)
    assert snapshot is not None
    assert snapshot.status == JobStatus.SUCCEEDED
    assert snapshot.results and snapshot.results[0].passed is True
    assert snapshot.test_statuses[definition.qualified_name] == TestStatus.PASSED
    assert JobStatus.RUNNING in updates
    assert JobStatus.SUCCEEDED in updates


def test_job_queue_marks_job_failed_on_exception(monkeypatch) -> None:
    store = JobStore()

    def failing_execute(definition: TestDefinition) -> TestResult:  # pragma: no cover - exercised via exception
        raise RuntimeError(f"boom: {definition.qualified_name}")

    monkeypatch.setattr("goose.testing.api.jobs.job_queue.execute_test", failing_execute)

    queue = JobQueue(job_store=store)
    definition = _make_definition("failure")

    job = queue.enqueue([definition])
    queue._queue.join()  # type: ignore[attr-defined]

    snapshot = store.get_job(job.id)
    assert snapshot is not None
    assert snapshot.status == JobStatus.FAILED
    assert snapshot.error is not None and "boom" in snapshot.error
    assert snapshot.test_statuses[definition.qualified_name] == TestStatus.FAILED
