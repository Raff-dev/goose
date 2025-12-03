"""Command-line entrypoints for Goose.

This module exposes a single ``goose`` command implemented with Typer.

End-users interact with the installed console script::

    goose run example_tests.test_agent_behaviour
    goose run --list example_tests.test_agent_behaviour.test_case
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import typer
from typer import colors

from goose.api.config import set_tests_root
from goose.testing.discovery import load_from_qualified_name
from goose.testing.models.tests import TestResult
from goose.testing.runner import execute_test

app = typer.Typer(help="Goose LLM testing CLI")


def _resolve_tests_root(target: str) -> Path:
    """Resolve and validate the tests root path from *target*."""
    root_token = target.split(".", 1)[0]
    root_path = Path(root_token)
    if not root_path.is_absolute():
        root_path = Path.cwd() / root_path
    if not root_path.exists():
        raise typer.BadParameter(f"Tests root '{root_path}' does not exist")
    return root_path


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
    target: str = typer.Argument(..., help="Dotted module or module.function identifying Goose tests"),
    list_only: bool = typer.Option(False, "--list", help="List discovered tests without executing them"),
    verbose: bool = typer.Option(
        False,
        "-v",
        "--verbose",
        help="Display conversational transcripts including human prompts, agent replies, and tool activity",
    ),
) -> None:
    """Resolve *target* to one or more tests and optionally execute them.

    When ``--list`` is provided the command only prints the qualified
    names of discovered tests. Otherwise each test is executed in the
    order returned by the discovery engine, with pass/fail totals
    emitted at the end.
    """
    set_tests_root(_resolve_tests_root(target))

    try:
        definitions = load_from_qualified_name(target)
    except ValueError as error:
        raise typer.BadParameter(str(error)) from error

    if list_only:
        for definition in definitions:
            typer.echo(definition.qualified_name)
        raise typer.Exit(code=0)

    passed_count, failures, total_duration = _run_tests(definitions, verbose)

    passed_text = typer.style(str(passed_count), fg=colors.GREEN)
    failed_text = typer.style(str(failures), fg=colors.RED)
    duration_text = typer.style(f"{total_duration:.2f}s", fg=colors.CYAN)
    typer.echo(f"{passed_text} passed, {failed_text} failed ({duration_text})")

    raise typer.Exit(code=1 if failures else 0)


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
    # pylint: disable=too-many-branches,too-many-statements

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
