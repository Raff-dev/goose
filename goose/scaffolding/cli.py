"""Scaffolding CLI commands for initializing Goose projects."""

from __future__ import annotations

import shutil
from pathlib import Path

import typer

# Template directory is located alongside this module
TEMPLATE_DIR = Path(__file__).parent / "template"

app = typer.Typer(help="Initialize Goose projects")


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
    """Initialize a gooseapp/ folder with starter files."""
    base_path = path if path else Path.cwd()
    gooseapp_dir = base_path / "gooseapp"

    # Check if already exists
    if gooseapp_dir.exists() and not force:
        typer.echo(f"Directory {gooseapp_dir} already exists. Use --force to overwrite.", err=True)
        raise typer.Exit(code=1)

    # Remove existing directory if force is set
    if gooseapp_dir.exists() and force:
        shutil.rmtree(gooseapp_dir)

    # Copy template directory
    shutil.copytree(TEMPLATE_DIR, gooseapp_dir)

    typer.echo(f"Created {gooseapp_dir}/")
    for file_path in sorted(gooseapp_dir.rglob("*.py")):
        relative = file_path.relative_to(gooseapp_dir)
        typer.echo(f"  ├── {relative}")

    typer.echo("")
    typer.echo("✨ Goose app initialized!")
    typer.echo("")
    typer.echo("Next steps:")
    typer.echo("  1. Edit gooseapp/app.py to add your tools and configure reload targets")
    typer.echo("  2. Edit gooseapp/conftest.py to wire up your agent's query function")
    typer.echo("  3. Create tests in gooseapp/tests/ (see test_example.py for patterns)")
    typer.echo("  4. Run: goose api")
