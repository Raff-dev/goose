"""Validation errors and error classification for Goose test results.

This module contains exceptions raised during test validation (tool call checks,
expectation validation) and the ErrorType enum used to classify test failures.
"""

from __future__ import annotations

from enum import Enum


class ToolCallValidationError(Exception):
    """Custom exception for tool call validation errors."""

    def __init__(self, expected_tool_calls: set[str], actual_tool_calls: set[str]) -> None:
        self.expected_tool_calls = expected_tool_calls
        self.actual_tool_calls = actual_tool_calls
        super().__init__(expected_tool_calls, actual_tool_calls)

    def __str__(self) -> str:  # pragma: no cover - simple delegation
        return f"Expected tool calls: {self.expected_tool_calls}, but got: {self.actual_tool_calls}"


class ExpectationValidationError(Exception):
    """Custom exception for expectation validation errors."""

    def __init__(
        self, reasoning: str, expectations_unmet: list[str], failure_reasons: dict[str, str] | None = None
    ) -> None:
        self.reasoning = reasoning
        self.expectations_unmet = expectations_unmet
        self.failure_reasons = failure_reasons or {}
        super().__init__(reasoning, expectations_unmet)

    def __str__(self) -> str:  # pragma: no cover - simple delegation
        return f"Expectations not met: {self.expectations_unmet}\n\n{self.reasoning}"


class ErrorType(str, Enum):
    """Stable classification labels for Goose test failures."""

    EXPECTATION = "expectation"
    VALIDATION = "validation"
    TOOL_CALL = "tool_call"
    UNEXPECTED = "unexpected"
