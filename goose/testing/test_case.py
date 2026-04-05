"""Test case implementation for Goose testing."""

from __future__ import annotations

import inspect
from collections.abc import Callable, Mapping
from typing import Any, NoReturn, Protocol

from goose.testing.errors import ExpectationValidationError, ToolCallValidationError
from goose.testing.models.messages import AgentResponse
from goose.testing.validator import ExpectationsEvaluationResponse


class SupportsToolName(Protocol):
    """Protocol for objects exposing a stable tool name."""

    name: str


ExpectedToolCall = str | Mapping[str, Any] | SupportsToolName | Callable[..., Any]


def _raise_invalid_expected_tool_call(item: object) -> NoReturn:
    item_type = type(item).__name__
    raise TypeError(
        "expected_tool_calls items must be a tool name string, an object with a non-empty "
        ".name attribute, a callable tool function, or an OpenAI-style tool dict with "
        "'name' or 'function.name'. "
        f"Got {item_type}: {item!r}."
    )


def _extract_expected_tool_call_name(item: ExpectedToolCall) -> str:
    if isinstance(item, str):
        name = item.strip()
        if name:
            return name
        _raise_invalid_expected_tool_call(item)

    if isinstance(item, Mapping):
        direct_name = item.get("name")
        if isinstance(direct_name, str):
            direct_name = direct_name.strip()
            if direct_name:
                return direct_name

        function_payload = item.get("function")
        if isinstance(function_payload, Mapping):
            nested_name = function_payload.get("name")
            if isinstance(nested_name, str):
                nested_name = nested_name.strip()
                if nested_name:
                    return nested_name

        _raise_invalid_expected_tool_call(item)

    raw_name = getattr(item, "name", None)
    if isinstance(raw_name, str):
        normalized_name = raw_name.strip()
        if normalized_name:
            return normalized_name

    if inspect.ismodule(item):
        _raise_invalid_expected_tool_call(item)

    if callable(item):
        callable_name = getattr(item, "__name__", None)
        if isinstance(callable_name, str):
            callable_name = callable_name.strip()
            if callable_name:
                return callable_name

    _raise_invalid_expected_tool_call(item)


class TestCase:
    """Represents a single test case for agent behavior validation."""

    __test__ = False

    def __init__(
        self,
        query_message: str,
        expectations: list[str],
        *,
        expected_tool_calls: list[ExpectedToolCall] | None = None,
    ):
        self.query_message = query_message
        self.expectations = expectations
        self.expected_tool_calls = expected_tool_calls
        self.last_response: AgentResponse | None = None

        # Validate expected_tool_calls contains actual tools
        if expected_tool_calls:
            for item in expected_tool_calls:
                _extract_expected_tool_call_name(item)

    @property
    def expected_tool_call_names(self) -> list[str]:
        """Return the names of the expected tool calls."""
        if not self.expected_tool_calls:
            return []
        return [_extract_expected_tool_call_name(tool) for tool in self.expected_tool_calls]

    def validate_tool_calls(self, actual_tool_call_names: list[str]) -> None:
        """Ensure that expected tool calls were made.

        Only fails if expected tools are missing. Extra tool calls are allowed.
        """
        if self.expected_tool_calls is None:
            return

        expected_tool_call_names_set = set(self.expected_tool_call_names)
        actual_tool_call_names_set = set(actual_tool_call_names)

        missing_tools = expected_tool_call_names_set - actual_tool_call_names_set
        if missing_tools:
            raise ToolCallValidationError(
                expected_tool_calls=expected_tool_call_names_set,
                actual_tool_calls=actual_tool_call_names_set,
            )

    def validate_expectations(self, evaluation: ExpectationsEvaluationResponse) -> None:
        """Ensure that expected expectations were met."""
        unmet_expectations = [
            self.expectations[index - 1]
            for index in evaluation.unmet_expectation_numbers
            if 1 <= index <= len(self.expectations)
        ]

        if unmet_expectations:
            # Map expectation numbers to expectation text for failure_reasons
            failure_reasons = {
                self.expectations[index - 1]: reason
                for index, reason in evaluation.failure_reasons.items()
                if 1 <= index <= len(self.expectations)
            }
            raise ExpectationValidationError(
                reasoning=evaluation.reasoning,
                expectations_unmet=unmet_expectations,
                failure_reasons=failure_reasons,
            )
