from __future__ import annotations

from collections.abc import Iterator
from datetime import datetime, timedelta, timezone

from goose.testing.api.jobs.enums import JobStatus, TestStatus
from goose.testing.api.jobs.state import JobStore
from goose.testing.models.tests import TestDefinition, TestResult


def _make_definition(name: str = "test_case") -> TestDefinition:
    def _case() -> None:  # pragma: no cover - helper only
        return None

    return TestDefinition(module="pkg.tests", name=name, func=_case)


def test_create_job_initializes_snapshot(monkeypatch) -> None:
    store = JobStore()
    definition = _make_definition()

    job = store.create_job(targets=[definition])

    assert job.status == JobStatus.QUEUED
    assert job.test_statuses == {definition.qualified_name: TestStatus.QUEUED}
    assert job.results == []


def test_get_job_returns_copy() -> None:
    store = JobStore()
    definition = _make_definition()
    job = store.create_job(targets=[definition])

    fetched = store.get_job(job.id)
    assert fetched is not None
    fetched.test_statuses[definition.qualified_name] = TestStatus.FAILED

    # Original should remain untouched because fetch returns a deepcopy
    original = store.get_job(job.id)
    assert original is not None
    assert original.test_statuses[definition.qualified_name] == TestStatus.QUEUED


def test_list_jobs_sorted_descending(monkeypatch) -> None:
    timestamps: Iterator[datetime] = iter(
        datetime(2024, 1, 1, tzinfo=timezone.utc) + timedelta(seconds=offset) for offset in range(3)
    )

    class StubDateTime(datetime):
        @classmethod
        def now(cls, tz=None):  # type: ignore[override]
            _ = tz  # timezone already baked into timestamps
            return next(timestamps)

    monkeypatch.setattr("goose.testing.api.jobs.state.datetime", StubDateTime)  # type: ignore[arg-type]

    store = JobStore()
    first = store.create_job(targets=[_make_definition("first")])
    second = store.create_job(targets=[_make_definition("second")])

    jobs = store.list_jobs()
    assert [job.id for job in jobs] == [second.id, first.id]


def test_mark_running_updates_statuses() -> None:
    store = JobStore()
    defs = [_make_definition("alpha"), _make_definition("beta")]
    job = store.create_job(targets=defs)

    running = store.mark_running(job.id)
    assert running is not None
    assert running.status == JobStatus.RUNNING
    assert running.test_statuses[defs[0].qualified_name] == TestStatus.RUNNING
    assert running.test_statuses[defs[1].qualified_name] == TestStatus.QUEUED


def test_mark_succeeded_persists_results() -> None:
    store = JobStore()
    definition = _make_definition()
    job = store.create_job(targets=[definition])

    result = TestResult(definition=definition, duration=0.1, test_case=None, exception=None)
    snapshot = store.mark_succeeded(job.id, [result])
    assert snapshot is not None
    assert snapshot.status == JobStatus.SUCCEEDED
    assert snapshot.results[0].passed is True
    assert snapshot.test_statuses[definition.qualified_name] == TestStatus.PASSED


def test_mark_failed_records_error() -> None:
    store = JobStore()
    definition = _make_definition()
    job = store.create_job(targets=[definition])

    snapshot = store.mark_failed(job.id, "boom")
    assert snapshot is not None
    assert snapshot.status == JobStatus.FAILED
    assert snapshot.error == "boom"
    assert snapshot.test_statuses[definition.qualified_name] == TestStatus.FAILED


def test_update_test_status_overrides_single_entry() -> None:
    store = JobStore()
    definition = _make_definition()
    job = store.create_job(targets=[definition])

    updated = store.update_test_status(job.id, definition.qualified_name, TestStatus.RUNNING)
    assert updated is not None
    assert updated.test_statuses[definition.qualified_name] == TestStatus.RUNNING
