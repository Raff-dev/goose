"""Testing subcommands for Goose CLI.

This module provides the `goose test` subcommand group for running
and listing Goose tests from the command line.
"""

from __future__ import annotations

import typer
from typer import colors

from goose.core.config import GooseConfig
from goose.testing.discovery import load_from_qualified_name
from goose.testing.output import run_tests

app = typer.Typer(help="Run and manage Goose tests")


@app.command()
def run(
    target: str = typer.Argument(
        None,
        help="Dotted test path (e.g., 'gooseapp.tests.test_foo'). Defaults to all tests.",
    ),
    verbose: bool = typer.Option(
        False,
        "-v",
        "--verbose",
        help="Display conversational transcripts including human prompts, agent replies, and tool activity",
    ),
) -> None:
    """Run Goose tests from the command line.

    Uses the fixed gooseapp/ structure. If no target is specified,
    runs all tests in gooseapp.tests.
    """
    config = GooseConfig()
    test_target = target or config.TESTS_MODULE

    try:
        definitions = load_from_qualified_name(test_target)
    except ValueError as error:
        raise typer.BadParameter(str(error)) from error

    passed_count, failures, total_duration = run_tests(definitions, verbose)

    passed_text = typer.style(str(passed_count), fg=colors.GREEN)
    failed_text = typer.style(str(failures), fg=colors.RED)
    duration_text = typer.style(f"{total_duration:.2f}s", fg=colors.CYAN)
    typer.echo(f"{passed_text} passed, {failed_text} failed ({duration_text})")

    raise typer.Exit(code=1 if failures else 0)


@app.command("list")
def list_tests(
    target: str = typer.Argument(
        None,
        help="Dotted test path (e.g., 'gooseapp.tests.test_foo'). Defaults to all tests.",
    ),
) -> None:
    """List discovered Goose tests without executing them."""
    config = GooseConfig()
    test_target = target or config.TESTS_MODULE

    try:
        definitions = load_from_qualified_name(test_target)
    except ValueError as error:
        raise typer.BadParameter(str(error)) from error

    for definition in definitions:
        typer.echo(definition.qualified_name)

    raise typer.Exit(code=0)
