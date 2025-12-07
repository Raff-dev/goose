"""CLI output helpers for displaying test results.

This module provides formatting and display utilities for rendering
test results in the terminal.
"""

from __future__ import annotations

import json
from typing import Any

from typer import colors, echo, style

from goose.testing.models.tests import TestResult
from goose.testing.runner import execute_test


def run_tests(definitions: list, verbose: bool) -> tuple[int, int, float]:
    """Execute tests and return (passed, failures, total_duration)."""
    failures = 0
    total = 0
    total_duration = 0.0
    for definition in definitions:
        result = execute_test(definition)
        total += 1
        total_duration += result.duration
        failures += display_result(result, verbose=verbose)
    return total - failures, failures, total_duration


def display_result(result: TestResult, *, verbose: bool) -> int:
    """Render a single test result and report whether it failed."""
    if result.passed:
        status_label = "PASS"
        status_color = colors.GREEN
    else:
        status_label = "FAIL"
        status_color = colors.RED

    status_text = style(status_label, fg=status_color)
    duration_text = style(f"{result.duration:.2f}s", fg=colors.CYAN)
    echo(f"{status_text} {result.name} ({duration_text})")

    if verbose:
        _display_verbose_details(result)

    if not result.passed:
        assert result.error_type is not None
        divider = style("-" * 40, fg=colors.WHITE)
        marker = style(f"[ERROR: {result.error_type.value}]", fg=colors.RED)
        body = style(result.error_message, fg=colors.RED)

        echo(divider)
        echo(f"{marker} {body}")
        echo(divider)

    if result.passed:
        return 0

    return 1


def _display_verbose_details(result: TestResult) -> None:  # pylint: disable=too-many-branches,too-many-statements
    """Emit conversational details for verbose runs."""
    test_case = result.test_case
    header = style("Conversation", fg=colors.CYAN, bold=True)
    echo(header)

    if test_case is None:
        echo("No test case data recorded.")
        return

    response = test_case.last_response
    if response is None:
        echo("No agent response captured.")
        echo(test_case.query_message)
        return

    rendered_human = False
    for message in response.messages:
        if message.type == "human":
            rendered_human = True
            label = style("Human", fg=colors.BLUE)
            echo(label)
            echo(message.content)
            echo("")
            continue
        if message.type == "ai":
            label = style("Agent", fg=colors.GREEN)
            echo(label)
            if message.content:
                echo("Response:")
                echo(message.content)
            if message.tool_calls:
                echo("Tool Calls:")
                for tool_call in message.tool_calls:
                    echo(f"- {tool_call.name}")
                    if tool_call.args:
                        echo("Args:")
                        echo(_format_json_data(tool_call.args))
                    if tool_call.id:
                        echo(f"Id: {tool_call.id}")
                    echo("")
            else:
                echo("")
            continue
        if message.type == "tool":
            tool_name = "tool"
            if message.tool_name is not None:
                tool_name = message.tool_name
            label = style(f"Tool Result ({tool_name})", fg=colors.MAGENTA)
            echo(label)
            echo(_format_json_text(message.content))
            echo("")
            continue
        label = style(message.type.title(), fg=colors.YELLOW)
        echo(label)
        echo(message.content)
        echo("")

    if not rendered_human and test_case.query_message:
        label = style("Human", fg=colors.BLUE)
        echo(label)
        echo(test_case.query_message)


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
