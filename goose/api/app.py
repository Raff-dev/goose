"""FastAPI application factory for Goose."""

from __future__ import annotations

from pathlib import Path

import typer
from fastapi import FastAPI  # type: ignore[import-not-found]
from fastapi.middleware.cors import CORSMiddleware  # type: ignore[import-not-found]
from uvicorn import Config, Server

from goose.api.config import set_tests_root
from goose.api.routes import router

app = FastAPI(title="Goose API", version="0.1.0")
cli = typer.Typer(help="Run the Goose FastAPI server.")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@cli.command()
def serve(
    tests_path: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True,
        resolve_path=True,
        help="Directory containing Goose tests for discovery",
    ),
    host: str = typer.Option("127.0.0.1", "--host", help="Host interface to bind"),
    port: int = typer.Option(8000, "--port", help="Port to bind"),
    reload: bool = typer.Option(
        False,
        "--reload/--no-reload",
        help="Enable autoreload for development",
        show_default=True,
    ),
) -> None:
    """Launch the Goose FastAPI server via uvicorn."""

    resolved_tests = tests_path.resolve()
    set_tests_root(resolved_tests)
    config = Config(app=app, host=host, port=port, reload=reload)
    server = Server(config)
    raise SystemExit(server.run())


def main() -> None:
    """Compatibility wrapper for invoking the Typer CLI."""

    cli()


__all__ = ["app", "cli", "main"]
