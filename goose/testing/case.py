"""Test case representation for Goose agent validation."""

from __future__ import annotations

from langchain_core.tools import BaseTool

from goose.agent_validator import ValidationResult
from goose.models import AgentResponse
from goose.testing.retry import RetryConfig


class TestCase:  # pylint: disable=too-many-instance-attributes
    """Represents a single test case for agent behavior validation."""

    def __init__(
        self,
        query: str,
        expectations: list[str],
        *,
        expected_tool_calls: list[BaseTool] | None = None,
        retry: RetryConfig | None = None,
    ):  # pylint: disable=too-many-arguments
        self.query = query
        self.expectations = expectations
        self.expected_tool_calls = list(expected_tool_calls) if expected_tool_calls is not None else None
        retry_config = retry or RetryConfig()
        self.attempts = max(1, int(retry_config.attempts))
        self.sleep_between_attempts = float(retry_config.sleep_between_attempts)
        self._result: ValidationResult | None = None
        self.last_response: AgentResponse | None = None

    def record_result(self, result: ValidationResult) -> None:
        """Persist the latest validation result."""

        self._result = result

    def get_result(self) -> ValidationResult | None:
        """Return the cached validation result if available."""

        return self._result

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
