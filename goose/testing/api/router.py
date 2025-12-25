from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, status  # type: ignore[import-not-found]

from goose.core.config import GooseConfig
from goose.testing.api.jobs import JobNotifier, JobQueue
from goose.testing.api.jobs.job_target_resolver import resolve_targets
from goose.testing.api.persistence import TestRunStore
from goose.testing.api.schema import JobResource, RunRequest, TestResultModel, TestSummary
from goose.testing.discovery import load_from_qualified_name
from goose.testing.models.tests import TestResult

router = APIRouter()

notifier = JobNotifier()


def _get_data_path() -> Path:
    """Return the data directory path for persisting test results."""
    config = GooseConfig()
    return config.gooseapp_dir / "data"


test_run_store = TestRunStore(_get_data_path())


def _on_result_added(job_id: str, result: TestResult) -> None:
    """Callback for when a test result is added - persists to disk."""
    result_model = TestResultModel.from_result(result)
    test_run_store.add_run(job_id, result_model)


job_queue = JobQueue(on_job_update=notifier.publish, on_result_added=_on_result_added)


@router.get("/tests", response_model=list[TestSummary])
def get_tests() -> list[TestSummary]:
    """Return metadata for all discovered Goose tests."""
    definitions = load_from_qualified_name(GooseConfig.TESTS_MODULE)
    return [TestSummary.from_definition(definition) for definition in definitions]


@router.post("/runs", response_model=JobResource, status_code=status.HTTP_202_ACCEPTED)
def create_run(payload: RunRequest | None = None) -> JobResource:
    """Schedule execution for all tests or a targeted subset."""
    request = payload or RunRequest()
    targets = resolve_targets(request.tests)
    job = job_queue.enqueue(targets)
    return JobResource.from_job(job)


@router.get("/runs", response_model=list[JobResource])
def list_runs() -> list[JobResource]:
    """Return snapshots for all known execution jobs."""

    jobs = job_queue.list_jobs()
    return [JobResource.from_job(job) for job in jobs]


@router.get("/runs/{job_id}", response_model=JobResource)
def get_run(job_id: str) -> JobResource:
    """Return status details for a single execution job."""

    job = job_queue.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return JobResource.from_job(job)


@router.websocket("/ws/runs")
async def runs_stream(websocket: WebSocket) -> None:
    """Stream job updates to connected clients."""

    await websocket.accept()
    queue = notifier.subscribe()
    try:
        snapshot = job_queue.list_jobs()
        payload = {
            "type": "snapshot",
            "jobs": [JobResource.from_job(job).model_dump(mode="json") for job in snapshot],
        }
        await websocket.send_text(json.dumps(payload))

        while True:
            job_snapshot = await queue.get()
            job_resource = JobResource.from_job(job_snapshot)
            await websocket.send_text(json.dumps({"type": "job", "job": job_resource.model_dump(mode="json")}))
    except WebSocketDisconnect:
        pass
    finally:
        notifier.unsubscribe(queue)


@router.get("/history", response_model=dict[str, TestResultModel])
def get_history() -> dict[str, TestResultModel]:
    """Return the latest result for each test from persisted history."""
    return test_run_store.get_latest_results()


@router.get("/history/{qualified_name:path}", response_model=list[TestResultModel])
def get_test_history(qualified_name: str) -> list[TestResultModel]:
    """Return all historical results for a specific test, oldest first."""
    runs = test_run_store.get_runs_for_test(qualified_name)
    return [run.result for run in runs]


@router.delete("/history", status_code=status.HTTP_204_NO_CONTENT)
def clear_history() -> None:
    """Clear all persisted test run history."""
    test_run_store.clear()


@router.delete("/history/{qualified_name:path}/{index}", status_code=status.HTTP_204_NO_CONTENT)
def delete_test_run(qualified_name: str, index: int) -> None:
    """Delete a specific run by index (0-based, oldest first)."""
    success = test_run_store.delete_run_at_index(qualified_name, index)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")


@router.delete("/history/{qualified_name:path}", status_code=status.HTTP_204_NO_CONTENT)
def clear_test_history(qualified_name: str) -> None:
    """Clear all history for a specific test."""
    test_run_store.clear_test_history(qualified_name)


__all__ = ["router"]
