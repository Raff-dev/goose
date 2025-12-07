"""Exception handlers for the Goose API."""

from __future__ import annotations

import traceback

from fastapi import FastAPI, Request, status  # type: ignore[import-not-found]
from fastapi.responses import JSONResponse  # type: ignore[import-not-found]

from goose.testing.exceptions import TestLoadError, UnknownTestError


def register_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers on the FastAPI app."""

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

    @app.exception_handler(Exception)
    async def generic_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
        """Handle any unhandled exceptions with detailed traceback."""
        tb = traceback.format_exception(type(exc), exc, exc.__traceback__)
        detail = "".join(tb)
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"detail": detail})
