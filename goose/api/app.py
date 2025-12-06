"""FastAPI application factory for Goose."""

from __future__ import annotations

import traceback

from fastapi import FastAPI, Request, status  # type: ignore[import-not-found]
from fastapi.middleware.cors import CORSMiddleware  # type: ignore[import-not-found]
from fastapi.responses import JSONResponse  # type: ignore[import-not-found]

from goose.api.routes import router as testing_router
from goose.testing.exceptions import TestLoadError, UnknownTestError
from goose.tooling.api.router import router as tooling_router

app = FastAPI(title="Goose API", version="0.1.0")


@app.get("/health")
def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "ok"}


@app.exception_handler(TestLoadError)
async def test_load_error_handler(_request: Request, exc: TestLoadError) -> JSONResponse:
    """Handle test loading errors (syntax errors, missing imports, etc.)."""
    cause = exc.__cause__
    if cause is not None:
        tb = traceback.format_exception(type(cause), cause, cause.__traceback__)
        detail = f"{exc.message}:\n\n{''.join(tb)}"
    else:
        detail = exc.message
    return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content={"detail": detail})


@app.exception_handler(UnknownTestError)
async def unknown_test_error_handler(_request: Request, exc: UnknownTestError) -> JSONResponse:
    """Handle requests for tests that don't exist."""
    return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": str(exc)})


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount testing routes under /testing prefix
app.include_router(testing_router, prefix="/testing", tags=["testing"])

# Mount tooling routes under /tooling prefix
app.include_router(tooling_router, prefix="/tooling", tags=["tooling"])


__all__ = ["app"]
