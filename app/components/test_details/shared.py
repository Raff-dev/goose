"""Shared helpers for test detail views."""

from __future__ import annotations

import inspect
from collections.abc import Sequence

from goose.testing import TestDefinition
from goose.testing.types import ExecutionRecord, TestResult

STATUS_COLORS: dict[str, str] = {
    "Error": "#dc2626",
    "Not run": "#64748b",
    "Passed": "#16a34a",
    "Failed": "#dc2626",
    "Running": "#0ea5e9",
}


def format_test_title(name: str) -> str:
    """Return a human-readable title derived from a test function name."""

    cleaned = name.replace("_", " ").strip()
    return cleaned.title() if cleaned else name


def get_test_summary(definition: TestDefinition) -> str:
    """Extract the first line of a test's docstring to use as a summary."""

    docstring = inspect.getdoc(definition.func)
    if not docstring:
        return ""
    return docstring.strip().splitlines()[0]


# pylint: disable=too-many-return-statements
def failure_summary(result: TestResult | None, test_error: str | None) -> str:
    """Summarize why a test failed using a concise categorical label."""

    if test_error:
        return "Unexpected error"

    if result is None or result.passed:
        return ""

    if any(execution.error for execution in result.executions):
        return "Unexpected error"

    if has_tool_mismatch(result.executions):
        return "Tool mismatch"

    if result.error:
        normalized_error = result.error.strip().lower()
        if "assert" in normalized_error:
            return "Assertion failure"
        return "Expectations unmet"

    if any(execution_validation_failed(execution) for execution in result.executions):
        return "Expectations unmet"

    return "Expectations unmet"


def duration_label(result: TestResult | None) -> str:
    """Format a duration label for display on test cards."""

    if result is None:
        return ""
    return f"Last duration: {result.duration * 1000:.0f} ms"


def status_label(result: TestResult | None, test_error: str | None) -> str:
    """Derive the overall status label for a test result and associated error state."""

    if test_error:
        return "Error"
    if result is None:
        return "Not run"
    return "Passed" if result.passed else "Failed"


def status_badge_text(status_label_value: str, result: TestResult | None, test_error: str | None) -> str:
    """Compose the text shown in a status badge for lists and detail views."""

    if result is None or test_error:
        return status_label_value
    return f"{status_label_value} · {result.duration:.2f}s"


def has_tool_mismatch(executions: Sequence[ExecutionRecord]) -> bool:
    """Determine whether any execution deviated from the expected tool call order."""

    for execution in executions:
        if not execution.expected_tool_calls:
            continue
        if execution.response is None:
            return True
        actual_calls = execution.response.tool_call_names
        if list(actual_calls) != list(execution.expected_tool_calls):
            return True
    return False


def execution_validation_failed(execution: ExecutionRecord) -> bool:
    """Check if a validator marked an execution as unsuccessful."""

    validation = execution.validation
    return validation is not None and not getattr(validation, "success", True)
