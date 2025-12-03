from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, status  # type: ignore[import-not-found]

from goose.api import config
from goose.api.jobs import JobNotifier, JobQueue, UnknownTestError
from goose.api.jobs.job_target_resolver import resolve_targets
from goose.api.schema import JobResource, RunRequest, TestSummary
from goose.testing.discovery import load_from_qualified_name

router = APIRouter()

notifier = JobNotifier()
job_queue = JobQueue(on_job_update=notifier.publish)


@router.get("/health")
def health() -> dict[str, str]:
    """Return a basic readiness probe response."""

    return {"status": "ok"}


@router.get("/tests", response_model=list[TestSummary])
def get_tests() -> list[TestSummary]:
    """Return metadata for all discovered Goose tests."""
    module_name = config.get_tests_root().name
    definitions = load_from_qualified_name(module_name)
    return [TestSummary.from_definition(definition) for definition in definitions]


@router.post("/runs", response_model=JobResource, status_code=status.HTTP_202_ACCEPTED)
def create_run(payload: RunRequest | None = None) -> JobResource:
    """Schedule execution for all tests or a targeted subset."""

    request = payload or RunRequest()
    try:
        targets = resolve_targets(request.tests)
        job = job_queue.enqueue(targets)
    except UnknownTestError as exc:  # pragma: no cover - validation depends on environment
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
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


__all__ = ["router"]
