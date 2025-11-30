"""Command-line entrypoints for Goose.

This module exposes a single ``goose`` command implemented with Typer.

End-users interact with the installed console script::

    goose run example_tests.test_agent_behaviour
    goose run --list example_tests.test_agent_behaviour.test_case
"""

from __future__ import annotations

import typer
from typer import colors

from goose.testing.discovery import load_from_qualified_name
from goose.testing.models.tests import TestResult
from goose.testing.runner import execute_test

app = typer.Typer(help="Goose LLM testing CLI")


@app.command()
def run(
    target: str = typer.Argument(..., help="Dotted module or module.function identifying Goose tests"),
    list_only: bool = typer.Option(False, "--list", help="List discovered tests without executing them"),
) -> None:
    """Resolve *target* to one or more tests and optionally execute them.

    When ``--list`` is provided the command only prints the qualified
    names of discovered tests. Otherwise each test is executed in the
    order returned by the discovery engine, with pass/fail totals
    emitted at the end.
    """

    try:
        definitions = load_from_qualified_name(target)
    except ValueError as error:
        raise typer.BadParameter(str(error)) from error

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
        assert result.error_type is not None
        divider = typer.style("-" * 40, fg=colors.WHITE)
        marker = typer.style(f"[ERROR: {result.error_type.value}]", fg=colors.RED)
        body = typer.style(result.error_message, fg=colors.RED)

        typer.echo(divider)
        typer.echo(f"{marker} {body}")
        typer.echo(divider)

    if result.passed:
        return 0

    return 1
