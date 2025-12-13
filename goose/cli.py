"""Main Goose CLI.

This module provides the unified `goose` command with subcommands:

    goose init                          # Create gooseapp/ folder
    goose api                           # Start dashboard server (auto-discovers gooseapp/)
    goose test run gooseapp.tests       # Run tests
    goose test list gooseapp.tests      # List tests
"""

from __future__ import annotations

from pathlib import Path

import typer
from uvicorn import Config, Server

from goose.app import app as fastapi_app
from goose.core.config import GooseConfig
from goose.scaffolding.cli import init
from goose.testing.cli import app as testing_app

app = typer.Typer(help="Goose - LLM agent development toolkit")

# Register subcommands
app.add_typer(testing_app, name="test")
app.command()(init)


# ============================================================================
# goose api
# ============================================================================


@app.command()
def api(
    host: str = typer.Option("127.0.0.1", "--host", help="Host interface to bind"),
    port: int = typer.Option(8730, "--port", help="Port to bind"),
) -> None:
    """Start the Goose dashboard server.

    Auto-discovers gooseapp/ in the current directory with the fixed structure:

        gooseapp/
        ├── app.py          # Must export `app = GooseApp(...)`
        ├── conftest.py     # Test fixtures
        └── tests/          # Test files

    Example:
        goose api
        goose api --port 3000
    """
    # Get singleton config and set base path
    config = GooseConfig()
    config.base_path = Path.cwd()

    # Validate gooseapp structure
    errors = config.validate()
    if errors:
        typer.echo("Error: Invalid gooseapp/ structure:", err=True)
        for error in errors:
            typer.echo(f"  - {error}", err=True)
        typer.echo("")
        typer.echo("Run 'goose init' to create the gooseapp/ structure.", err=True)
        raise typer.Exit(code=1)

    # Load the GooseApp
    try:
        config.load_app()
    except (ImportError, AttributeError, TypeError) as exc:
        typer.echo(f"Error loading gooseapp/app.py: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    # Set reload targets from app + always include gooseapp
    config.reload_targets = config.compute_reload_targets()

    typer.echo("Starting Goose dashboard")
    typer.echo(f"  Tests: {config.TESTS_MODULE}")
    typer.echo(f"  Reload targets: {config.reload_targets}")

    uvicorn_config = Config(app=fastapi_app, host=host, port=port, reload=True)
    server = Server(uvicorn_config)
    raise SystemExit(server.run())


if __name__ == "__main__":
    app()
