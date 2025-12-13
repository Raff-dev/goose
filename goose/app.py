"""FastAPI application factory for Goose."""

from __future__ import annotations

from fastapi import FastAPI  # type: ignore[import-not-found]
from fastapi.middleware.cors import CORSMiddleware  # type: ignore[import-not-found]

from goose.chatting.api.router import router as chatting_router
from goose.testing.api.exceptions import register_exception_handlers
from goose.testing.api.router import router as testing_router
from goose.tooling.api.router import router as tooling_router

app = FastAPI(title="Goose API", version="0.1.0")

# Register exception handlers
register_exception_handlers(app)

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

# Mount chatting routes under /chatting prefix
app.include_router(chatting_router, prefix="/chatting", tags=["chatting"])


__all__ = ["app"]
