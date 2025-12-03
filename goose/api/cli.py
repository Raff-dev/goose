"""Typer-powered CLI for running the Goose FastAPI server."""

from __future__ import annotations

from pathlib import Path

import typer
from uvicorn import Config, Server

from goose.api.app import app as fastapi_app
from goose.api.config import set_tests_root

app = typer.Typer(help="Run the Goose FastAPI server.")


@app.command()
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
    """Launch the Goose FastAPI server via uvicorn.

    Args:
        tests_path: Filesystem path containing Goose tests for discovery.
        host: Host interface to bind the uvicorn server to.
        port: Network port for the server to listen on.
        reload: Whether to enable code autoreload, usually in development.

    Returns:
        None: This function raises ``SystemExit`` after the server stops.
    """

    set_tests_root(tests_path)
    config = Config(app=fastapi_app, host=host, port=port, reload=reload)
    server = Server(config)
    raise SystemExit(server.run())


__all__ = ["app", "serve"]
