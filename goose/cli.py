"""Command-line entrypoints for Goose.

This module exposes a single ``goose`` command implemented with Typer.

End-users interact with the installed console script::

    goose run path/to/tests
    goose run --list path/to/tests
"""

from __future__ import annotations

from pathlib import Path

import typer
from typer import colors

from goose.testing.discovery import discover_tests
from goose.testing.imports import ensure_test_import_paths
from goose.testing.models.tests import TestResult
from goose.testing.runner import execute_test

app = typer.Typer(help="Goose LLM testing CLI")


@app.command()
def run(
    path: Path = typer.Argument(..., help="Directory containing Goose tests to discover"),
    list_only: bool = typer.Option(False, "--list", help="List discovered tests without executing them"),
) -> None:
    """Discover tests under *path* and optionally execute them.

    When ``--list`` is provided the command only prints the qualified
    names of discovered tests. Otherwise each test is executed in the
    order returned by the discovery engine, with pass/fail totals
    emitted at the end.
    """

    ensure_test_import_paths(path)

    definitions = discover_tests(path)

    if list_only:
        for definition in definitions:
            typer.echo(definition.qualified_name)
        raise typer.Exit(code=0)

    failures = 0
    total = 0
    total_duration = 0.0

    for definition in definitions:
        result = execute_test(definition)
        total += 1
        total_duration += result.duration
        failures += display_result(result)

    passed_count = total - failures
    passed_text = typer.style(str(passed_count), fg=colors.GREEN)
    failed_text = typer.style(str(failures), fg=colors.RED)
    duration_text = typer.style(f"{total_duration:.2f}s", fg=colors.CYAN)
    typer.echo(f"{passed_text} passed, {failed_text} failed ({duration_text})")

    if failures:
        raise typer.Exit(code=1)

    raise typer.Exit(code=0)


def display_result(result: TestResult) -> int:
    """Render a single test result and report whether it failed."""
    if result.passed:
        status_label = "PASS"
        status_color = colors.GREEN
    else:
        status_label = "FAIL"
        status_color = colors.RED

    status_text = typer.style(status_label, fg=status_color)
    duration_text = typer.style(f"{result.duration:.2f}s", fg=colors.CYAN)
    typer.echo(f"{status_text} {result.name} ({duration_text})")

    if not result.passed:
        divider = typer.style("-" * 40, fg=colors.WHITE)
        marker = typer.style(f"[ERROR: {result.error_type.value}]", fg=colors.RED)
        body = typer.style(result.error_message, fg=colors.RED)

        typer.echo(divider)
        typer.echo(f"{marker} {body}")
        typer.echo(divider)

    if result.passed:
        return 0

    return 1
