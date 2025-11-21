"""FastAPI application factory for Goose."""

from __future__ import annotations

import json

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, status  # type: ignore[import-not-found]
from fastapi.middleware.cors import CORSMiddleware  # type: ignore[import-not-found]

from goose.api.jobs import Job, JobNotifier, JobQueue, JobTargetResolver, UnknownTestError
from goose.api.schema import JobResource, RunRequest, TestSummary
from goose.testing.runner import list_tests


def create_app() -> FastAPI:
    """Construct and configure the Goose FastAPI application."""

    app = FastAPI(title="Goose API", version="0.1.0")

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:8001",
            "http://127.0.0.1:8001",
            "http://localhost:8002",
            "http://127.0.0.1:8002",
            "http://localhost:8003",
            "http://127.0.0.1:8003",
        ],  # Frontend URLs
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    notifier = JobNotifier()
    resolver = JobTargetResolver()

    def _publish_job(job: Job) -> None:
        notifier.publish(job)

    job_queue = JobQueue(on_job_update=_publish_job)

    @app.get("/health")
    def health() -> dict[str, str]:
        """Return a basic readiness probe response."""

        return {"status": "ok"}

    @app.get("/tests", response_model=list[TestSummary])
    def get_tests() -> list[TestSummary]:
        """Return metadata for all discovered Goose tests."""
        definitions = list_tests()
        return [TestSummary.from_definition(definition) for definition in definitions]

    @app.post("/runs", response_model=JobResource, status_code=status.HTTP_202_ACCEPTED)
    def create_run(payload: RunRequest | None = None) -> JobResource:
        """Schedule execution for all tests or a targeted subset."""

        request = payload or RunRequest()
        try:
            targets = resolver.resolve(request.tests)
            job = job_queue.enqueue(targets)
        except UnknownTestError as exc:  # pragma: no cover - validation depends on environment
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
        return JobResource.from_job(job)

    @app.get("/runs", response_model=list[JobResource])
    def list_runs() -> list[JobResource]:
        """Return snapshots for all known execution jobs."""

        jobs = job_queue.list_jobs()
        return [JobResource.from_job(job) for job in jobs]

    @app.get("/runs/{job_id}", response_model=JobResource)
    def get_run(job_id: str) -> JobResource:
        """Return status details for a single execution job."""

        job = job_queue.get_job(job_id)
        if job is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
        return JobResource.from_job(job)

    @app.websocket("/ws/runs")
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

    return app


__all__ = ["create_app"]
