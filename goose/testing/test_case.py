"""Test case implementation for Goose testing."""

from __future__ import annotations

from typing import TYPE_CHECKING

from langchain_core.tools import BaseTool

from goose.testing.errors import ExpectationValidationError, ToolCallValidationError
from goose.testing.validator import ExpectationsEvaluationResponse

if TYPE_CHECKING:
    from goose.testing.models.messages import AgentResponse


class TestCase:
    """Represents a single test case for agent behavior validation."""

    __test__ = False

    def __init__(
        self,
        query_message: str,
        expectations: list[str],
        *,
        expected_tool_calls: list[BaseTool] | None = None,
    ):
        self.query_message = query_message
        self.expectations = expectations
        self.expected_tool_calls = expected_tool_calls
        self.last_response: AgentResponse | None = None

        # Validate expected_tool_calls contains actual tools
        if expected_tool_calls:
            for item in expected_tool_calls:
                if not isinstance(item, BaseTool):
                    item_type = type(item).__name__
                    raise TypeError(
                        f"expected_tool_calls must contain BaseTool instances, got {item_type}: {item!r}. "
                        f"Make sure you're passing the tool function decorated with @tool, not a module."
                    )

    @property
    def expected_tool_call_names(self) -> list[str]:
        """Return the names of the expected tool calls."""
        if not self.expected_tool_calls:
            return []
        return [tool.name for tool in self.expected_tool_calls]

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
