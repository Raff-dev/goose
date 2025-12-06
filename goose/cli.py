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

from goose.testing.cli import app as testing_app

app = typer.Typer(help="Goose - LLM agent development toolkit")

# Register testing subcommands under "test"
app.add_typer(testing_app, name="test")


# ============================================================================
# goose init
# ============================================================================

GOOSEAPP_APP_TEMPLATE = '''\
"""Goose application configuration."""

from goose import GooseApp

# Import your tools here:
# from my_agent.tools import get_products, create_order

app = GooseApp(
    tools=[
        # get_products,
        # create_order,
    ],
    reload_targets=[
        # "my_agent",  # Add modules to hot-reload
    ],
)
'''

GOOSEAPP_CONFTEST_TEMPLATE = '''\
"""Goose test fixtures."""

from goose.testing import Goose, goose_fixture

# Import your app and agent:
# from gooseapp.app import app
# from my_agent.agent import query


@goose_fixture
def goose():
    """Create a Goose test fixture.

    Customize this fixture with your agent's query function and tools.
    """
    return Goose(
        # query_fn=query,
        # tools=app.tools,
        validator="gpt-4o-mini",
    )
'''


@app.command()
def init(
    path: Path | None = typer.Argument(
        None,
        help="Directory to create gooseapp in. Defaults to current directory.",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Overwrite existing files.",
    ),
) -> None:
    """Initialize a gooseapp/ folder with starter files.

    Creates:
        gooseapp/
        ├── app.py          # GooseApp configuration
        ├── conftest.py     # Test fixtures (at package root for discovery)
        └── tests/
            └── __init__.py
    """
    base_path = path if path else Path.cwd()
    gooseapp_dir = base_path / "gooseapp"
    tests_dir = gooseapp_dir / "tests"

    # Check if already exists
    if gooseapp_dir.exists() and not force:
        typer.echo(f"Directory {gooseapp_dir} already exists. Use --force to overwrite.", err=True)
        raise typer.Exit(code=1)

    # Create directories
    gooseapp_dir.mkdir(parents=True, exist_ok=True)
    tests_dir.mkdir(parents=True, exist_ok=True)

    # Create __init__.py files
    (gooseapp_dir / "__init__.py").write_text("")
    (tests_dir / "__init__.py").write_text("")

    # Create app.py
    app_file = gooseapp_dir / "app.py"
    app_file.write_text(GOOSEAPP_APP_TEMPLATE)
    typer.echo(f"Created {app_file}")

    # Create conftest.py at package root (required for discovery)
    conftest_file = gooseapp_dir / "conftest.py"
    conftest_file.write_text(GOOSEAPP_CONFTEST_TEMPLATE)
    typer.echo(f"Created {conftest_file}")

    typer.echo("")
    typer.echo("✨ Goose app initialized!")
    typer.echo("")
    typer.echo("Next steps:")
    typer.echo("  1. Edit gooseapp/app.py to add your tools")
    typer.echo("  2. Edit gooseapp/conftest.py to configure your fixture")
    typer.echo("  3. Create tests in gooseapp/tests/")
    typer.echo("  4. Run: goose api")


# ============================================================================
# goose api
# ============================================================================


@app.command()
def api(
    host: str = typer.Option("127.0.0.1", "--host", help="Host interface to bind"),
    port: int = typer.Option(8000, "--port", help="Port to bind"),
    reload: bool = typer.Option(
        False,
        "--reload/--no-reload",
        help="Enable autoreload for development",
        show_default=True,
    ),
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
        goose api --reload
    """
    from uvicorn import Config, Server

    from goose.api.app import app as fastapi_app
    from goose.api.config import GooseConfig

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

    uvicorn_config = Config(app=fastapi_app, host=host, port=port, reload=reload)
    server = Server(uvicorn_config)
    raise SystemExit(server.run())


if __name__ == "__main__":
    app()
