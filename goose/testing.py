"""Testing framework for validating agent behavior and tool usage."""

from __future__ import annotations

import asyncio
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from langchain_core.tools import BaseTool

from goose.agent_validator import AgentValidator, ValidationResult
from goose.models import AgentResponse


@dataclass(slots=True)
class RetryConfig:
    """Configuration for retrying flaky agent validations."""

    attempts: int = 1
    sleep_between_attempts: float = 0.0


class TestCase:
    """Represents a single test case for agent behavior validation."""

    def __init__(
        self,
        query: str,
        expectations: list[str],
        *,
        goose: Goose,
        expected_tool_calls: list[BaseTool] | None = None,
        retry: RetryConfig | None = None,
    ):  # pylint: disable=too-many-arguments
        self.query = query
        self.expectations = expectations
        self.expected_tool_calls = expected_tool_calls
        self.goose = goose
        retry_config = retry or RetryConfig()
        # Number of times to attempt running this test case (helpful for flaky LLM responses)
        self.attempts = max(1, int(retry_config.attempts))
        # Optional sleep (in seconds) between attempts
        self.sleep_between_attempts = float(retry_config.sleep_between_attempts)
        self._result: ValidationResult | None = None

    def validate_tool_calls(self, response: AgentResponse) -> ValidationResult:
        """Validate that the agent response contains the expected tool calls.

        Args:
            response: The parsed agent response to validate.

        Returns:
            ValidationResult indicating success or failure with reasoning.
        """
        if self.expected_tool_calls is None:
            return ValidationResult(success=True)

        actual_tool_calls = response.tool_call_names
        expected_tool_names = {tool.name for tool in self.expected_tool_calls}
        actual_tool_names = set(actual_tool_calls)

        if actual_tool_names != expected_tool_names or len(actual_tool_calls) != len(self.expected_tool_calls):
            return ValidationResult(
                success=False,
                reasoning=(f"Tool call mismatch. Expected {sorted(expected_tool_names)}, got {actual_tool_calls}"),
            )

        return ValidationResult(success=True)

    async def is_valid(self) -> bool:
        """Check if the test case passes validation.

        Returns:
            True if the test case passes, False otherwise.
        """
        if self._result is None:
            self._result = await self.goose.run(self)
        return self._result.success

    async def report(self) -> str:
        """Get the validation report for the test case.

        Returns:
            A string describing the test result and reasoning.
        """
        if self._result is None:
            self._result = await self.goose.run(self)
        return self._result.reasoning or ""


class Goose:
    """Testing framework for validating agent behavior and tool calls."""

    def __init__(self, agent_query_func: Callable[[str], dict[str, Any]]):
        self._agent_query_func = agent_query_func
        self._validation_agent = AgentValidator()

    async def run(self, test_case: TestCase) -> ValidationResult:
        """Execute a test case and validate the agent response.

        Args:
            test_case: The test case to execute.

        Returns:
            ValidationResult indicating success or failure with reasoning and timing.
        """
        last_reason: str | None = None
        for attempt in range(1, test_case.attempts + 1):
            start_time = time.time()
            raw_response = await asyncio.to_thread(self._agent_query_func, test_case.query)
            execution_time = time.time() - start_time

            # Parse the response using Pydantic
            response = AgentResponse.from_dict(raw_response)

            # Validate expectations
            evaluation = await asyncio.to_thread(self._validation_agent.validate, response, test_case.expectations)
            if evaluation.error:
                last_reason = evaluation.reasoning
            else:
                # Validate tool calls
                tool_call_validation = test_case.validate_tool_calls(response)
                if not tool_call_validation.success:
                    last_reason = tool_call_validation.reasoning
                else:
                    return ValidationResult(
                        success=True,
                        reasoning=f"Test passed in {execution_time:.2f}s on attempt {attempt}/{test_case.attempts}",
                    )

            # If we will retry, optionally sleep before next attempt
            if attempt < test_case.attempts and test_case.sleep_between_attempts > 0:
                time.sleep(test_case.sleep_between_attempts)

        # If we exhausted attempts, report failure with the last reasoning collected
        reason = last_reason or "Test failed after all attempts"
        return ValidationResult(success=False, reasoning=f"{reason} (after {test_case.attempts} attempts)")

    def case(
        self,
        query: str,
        expectations: list[str],
        *,
        expected_tool_calls: list[BaseTool] | None = None,
        retry: RetryConfig | None = None,
    ) -> TestCase:
        """Create a test case for validating agent behavior.

        Args:
            query: The query string to send to the agent.
            expectations: List of expected behaviors or outcomes.
            expected_tool_calls: Optional expected tool call sequence.
            retry: Optional retry configuration overriding defaults.

        Returns:
            A TestCase instance configured with the provided parameters.
        """
        return TestCase(
            query=query,
            expectations=expectations,
            goose=self,
            expected_tool_calls=expected_tool_calls,
            retry=retry,
        )
