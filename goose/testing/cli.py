"""Testing subcommands for Goose CLI.

This module provides the `goose test` subcommand group for running
and listing Goose tests from the command line.
"""

from __future__ import annotations

import json
from typing import Any

import typer
from typer import colors

from goose.api.config import GooseConfig
from goose.testing.discovery import load_from_qualified_name
from goose.testing.models.tests import TestResult
from goose.testing.runner import execute_test

app = typer.Typer(help="Run and manage Goose tests")


def _run_tests(definitions: list, verbose: bool) -> tuple[int, int, float]:
    """Execute tests and return (passed, failures, total_duration)."""
    failures = 0
    total = 0
    total_duration = 0.0
    for definition in definitions:
        result = execute_test(definition)
        total += 1
        total_duration += result.duration
        failures += _display_result(result, verbose=verbose)
    return total - failures, failures, total_duration


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

    passed_count, failures, total_duration = _run_tests(definitions, verbose)

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


def _display_result(result: TestResult, *, verbose: bool) -> int:
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

    if verbose:
        _display_verbose_details(result)

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


def _display_verbose_details(result: TestResult) -> None:
    """Emit conversational details for verbose runs."""
    test_case = result.test_case
    header = typer.style("Conversation", fg=colors.CYAN, bold=True)
    typer.echo(header)

    if test_case is None:
        typer.echo("No test case data recorded.")
        return

    response = test_case.last_response
    if response is None:
        typer.echo("No agent response captured.")
        typer.echo(test_case.query_message)
        return

    rendered_human = False
    for message in response.messages:
        if message.type == "human":
            rendered_human = True
            label = typer.style("Human", fg=colors.BLUE)
            typer.echo(label)
            typer.echo(message.content)
            typer.echo("")
            continue
        if message.type == "ai":
            label = typer.style("Agent", fg=colors.GREEN)
            typer.echo(label)
            if message.content:
                typer.echo("Response:")
                typer.echo(message.content)
            if message.tool_calls:
                typer.echo("Tool Calls:")
                for tool_call in message.tool_calls:
                    typer.echo(f"- {tool_call.name}")
                    if tool_call.args:
                        typer.echo("Args:")
                        typer.echo(_format_json_data(tool_call.args))
                    if tool_call.id:
                        typer.echo(f"Id: {tool_call.id}")
                    typer.echo("")
            else:
                typer.echo("")
            continue
        if message.type == "tool":
            tool_name = "tool"
            if message.tool_name is not None:
                tool_name = message.tool_name
            label = typer.style(f"Tool Result ({tool_name})", fg=colors.MAGENTA)
            typer.echo(label)
            typer.echo(_format_json_text(message.content))
            typer.echo("")
            continue
        label = typer.style(message.type.title(), fg=colors.YELLOW)
        typer.echo(label)
        typer.echo(message.content)
        typer.echo("")

    if not rendered_human and test_case.query_message:
        label = typer.style("Human", fg=colors.BLUE)
        typer.echo(label)
        typer.echo(test_case.query_message)


def _format_json_data(data: Any) -> str:
    """Return pretty JSON for structured data."""
    try:
        return json.dumps(data, indent=2, sort_keys=True)
    except TypeError:
        return str(data)


def _format_json_text(payload: str) -> str:
    """Render JSON strings with indentation when possible."""
    try:
        parsed = json.loads(payload)
    except (TypeError, json.JSONDecodeError):
        return payload
    return _format_json_data(parsed)
