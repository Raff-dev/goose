"""Shared ErrorType enum used across testing and API modules."""

from __future__ import annotations

from enum import Enum


class ToolCallValidationError(Exception):
    """Custom exception for tool call validation errors."""

    def __init__(self, expected_tool_calls: set[str], actual_tool_calls: set[str]) -> None:
        self.expected_tool_calls = expected_tool_calls
        self.actual_tool_calls = actual_tool_calls
        super().__init__(self.message())

    def message(self) -> str:
        return f"Expected tool calls: {self.expected_tool_calls}, " f"but got: {self.actual_tool_calls}"


class ExpectationValidationError(Exception):
    """Custom exception for expectation validation errors."""

    def __init__(self, reasoning: str, expectations_unmet: list[str]) -> None:
        self.reasoning = reasoning
        self.expectations_unmet = expectations_unmet
        super().__init__(self.message())

    def message(self) -> str:
        return f"Expectations not met: {self.expectations_unmet}\n\n{self.reasoning}"


class ErrorType(str, Enum):
    """Stable classification labels for Goose test failures."""

    EXPECTATION = "expectation"
    VALIDATION = "validation"
    TOOL_CALL = "tool_call"
    UNEXPECTED = "unexpected"
