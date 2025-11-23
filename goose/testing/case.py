"""Test case representation for Goose agent validation."""

from __future__ import annotations

from langchain_core.tools import BaseTool

from goose.testing.models import AgentResponse
from goose.testing.types import ValidationResult


class TestCase:  # pylint: disable=too-many-instance-attributes
    """Represents a single test case for agent behavior validation."""

    def __init__(
        self,
        query: str,
        expectations: list[str],
        *,
        expected_tool_calls: list[BaseTool] | None = None,
    ):
        self.query = query
        self.expectations = expectations
        self.expected_tool_calls = expected_tool_calls
        self.last_response: AgentResponse | None = None

    @property
    def expected_tool_names(self) -> list[str]:
        """Return the names of the expected tool calls."""
        if not self.expected_tool_calls:
            return []
        return [tool.name for tool in self.expected_tool_calls]

    def validate_tool_calls(self, response: AgentResponse) -> ValidationResult:
        """Ensure that expected tool calls were made."""

        if self.expected_tool_calls is None:
            return ValidationResult(success=True)

        actual_tool_calls = response.tool_call_names
        expected_tool_names = {tool.name for tool in self.expected_tool_calls}
        actual_tool_names = set(actual_tool_calls)

        if actual_tool_names != expected_tool_names or len(actual_tool_calls) != len(self.expected_tool_calls):
            return ValidationResult(
                success=False,
                reasoning=f"Tool call mismatch. Expected {sorted(expected_tool_names)}, got {actual_tool_calls}",
            )

        return ValidationResult(success=True)


__all__ = ["TestCase"]
