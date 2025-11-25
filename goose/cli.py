"""Command-line entrypoints for Goose.

This module exposes a single ``goose`` command implemented with Typer.

End-users interact with the installed console script::

    goose run path/to/tests
    goose run --list path/to/tests
"""

from __future__ import annotations

import sys
from pathlib import Path

import typer
from typer import colors

from goose.testing.discovery import discover_tests
from goose.testing.runner import execute_test
from goose.testing.types import TestResult

app = typer.Typer(help="Goose LLM testing CLI")


@app.command()
def run(
    path: str = typer.Argument(..., help="Directory containing Goose tests to discover"),
    list_only: bool = typer.Option(False, "--list", help="List discovered tests without executing them"),
) -> None:
    """Discover and run Goose tests under PATH.

    This mirrors the legacy ``goose run`` behavior and remains the
    default when the ``goose`` command is invoked without a subcommand.
    """

    target_path = Path(path)
    test_root = target_path.resolve()
    if test_root.is_file():
        test_root = test_root.parent

    for candidate in (test_root, test_root.parent):
        if str(candidate) not in sys.path:
            sys.path.insert(0, str(candidate))

    definitions = discover_tests(target_path)

    if list_only:
        for definition in definitions:
            typer.echo(definition.qualified_name)
        raise typer.Exit(code=0)

    failures = 0
    total = 0

    for definition in definitions:
        result = execute_test(definition)
        total += 1
        failures += display_result(result)

    passed_count = total - failures
    passed_text = typer.style(str(passed_count), fg=colors.GREEN)
    failed_text = typer.style(str(failures), fg=colors.RED)
    typer.echo(f"{passed_text} passed, {failed_text} failed")

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

    if result.error:
        divider = typer.style("-" * 40, fg=colors.WHITE)
        marker = typer.style("[ERROR]", fg=colors.RED)
        body = typer.style(result.error, fg=colors.RED)

        typer.echo(divider)
        typer.echo(f"{marker} {body}")
        typer.echo(divider)

    if result.passed:
        return 0

    return 1
