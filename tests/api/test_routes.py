from __future__ import annotations

from datetime import datetime, timezone

from fastapi.testclient import TestClient

from goose.api import routes
from goose.api.app import app
from goose.api.jobs.enums import JobStatus, TestStatus
from goose.api.jobs.models import Job
from goose.testing.models.tests import TestDefinition

client = TestClient(app)


def _make_definition(name: str = "test_example") -> TestDefinition:
    def _case() -> None:  # pragma: no cover - helper used in tests
        return None

    return TestDefinition(module="pkg.tests", name=name, func=_case)


def _make_job(status: JobStatus = JobStatus.QUEUED) -> Job:
    definition = _make_definition()
    now = datetime.now(timezone.utc)
    return Job(
        id="job-1",
        status=status,
        targets=[definition],
        created_at=now,
        updated_at=now,
        results=[],
        error=None,
        test_statuses={definition.qualified_name: TestStatus.QUEUED},
    )


def test_get_tests_returns_serialized_summaries(monkeypatch) -> None:
    definitions = [_make_definition("test_alpha"), _make_definition("test_beta")]
    monkeypatch.setattr(routes, "load_from_qualified_name", lambda *args, **kwargs: definitions)

    response = client.get("/tests")

    assert response.status_code == 200
    payload = response.json()
    assert [item["qualified_name"] for item in payload] == [
        "pkg.tests.test_alpha",
        "pkg.tests.test_beta",
    ]


def test_create_run_enqueues_targets(monkeypatch) -> None:
    definitions = [_make_definition()]
    job = _make_job(status=JobStatus.QUEUED)

    monkeypatch.setattr(routes, "resolve_targets", lambda tests: definitions)

    class DummyQueue:
        def __init__(self) -> None:
            self.targets = None

        def enqueue(self, targets):
            self.targets = targets
            return job

    dummy_queue = DummyQueue()
    monkeypatch.setattr(routes, "job_queue", dummy_queue, raising=False)

    response = client.post("/runs", json={"tests": ["pkg.tests.test_example"]})

    assert response.status_code == 202
    assert dummy_queue.targets == definitions
    payload = response.json()
    assert payload["id"] == job.id
    assert payload["tests"] == [definitions[0].qualified_name]


def test_list_runs_returns_job_resources(monkeypatch) -> None:
    job = _make_job(status=JobStatus.SUCCEEDED)

    class DummyQueue:
        def list_jobs(self):
            return [job]

    monkeypatch.setattr(routes, "job_queue", DummyQueue(), raising=False)

    response = client.get("/runs")

    assert response.status_code == 200
    payload = response.json()
    assert payload[0]["id"] == job.id
    assert payload[0]["status"] == JobStatus.SUCCEEDED.value


def test_get_run_returns_job(monkeypatch) -> None:
    job = _make_job(status=JobStatus.RUNNING)

    class DummyQueue:
        def get_job(self, job_id: str):
            return job if job_id == job.id else None

    monkeypatch.setattr(routes, "job_queue", DummyQueue(), raising=False)

    response = client.get(f"/runs/{job.id}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == job.id
    assert payload["status"] == JobStatus.RUNNING.value
