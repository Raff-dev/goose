"""CLI entrypoint for launching the Goose FastAPI server."""

from __future__ import annotations

import os

from uvicorn import Config, Server

from goose.api.app import create_app


def main() -> None:
    """Launch the Goose FastAPI server via uvicorn."""

    host = os.environ.get("GOOSE_API_HOST", "127.0.0.1")
    port = int(os.environ.get("GOOSE_API_PORT", "8000"))
    reload_enabled = os.environ.get("GOOSE_API_RELOAD", "false").lower() in {"1", "true", "yes"}

    test_settings = os.environ.get("GOOSE_TEST_SETTINGS")
    if test_settings:
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", test_settings)

    app = create_app()
    config = Config(app=app, host=host, port=port, reload=reload_enabled)
    server = Server(config)
    raise SystemExit(server.run())
