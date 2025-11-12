"""Core objects for Goose testing."""

from __future__ import annotations

import asyncio
import time
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Any

from langchain_core.tools import BaseTool

from goose.agent_validator import AgentValidator, ValidationResult
from goose.models import AgentResponse
from goose.testing.types import ExecutionRecord


@dataclass(slots=True)
class RetryConfig:
    """Configuration for retrying flaky agent validations."""

    attempts: int = 1
    sleep_between_attempts: float = 0.0


class Goose:
    """Testing helper that wraps the agent and validator logic."""

    def __init__(self, agent_query_func: Callable[[str], dict[str, Any]]):
        self._agent_query_func = agent_query_func
        self._validation_agent = AgentValidator()
        self._execution_history: list[ExecutionRecord] = []

    async def run(self, test_case: TestCase) -> ValidationResult:  # pylint: disable=too-many-locals
        """Execute a test case and return its validation result."""

        last_reason: str | None = None
        last_result: ValidationResult | None = None
        for attempt in range(1, test_case.attempts + 1):
            start_time = time.time()
            raw_response = await asyncio.to_thread(self._agent_query_func, test_case.query)
            execution_time = time.time() - start_time

            response = AgentResponse.from_dict(raw_response)
            test_case.last_response = response
            evaluation = await asyncio.to_thread(self._validation_agent.validate, response, test_case.expectations)

            if evaluation.error:
                last_result = ValidationResult(
                    success=False,
                    reasoning=evaluation.reasoning,
                    expectations_unmet=list(evaluation.expectations_unmet),
                    unmet_expectation_numbers=list(evaluation.unmet_expectation_numbers),
                )
                last_reason = last_result.reasoning
            else:
                tool_call_validation = test_case.validate_tool_calls(response)
                if tool_call_validation.success:
                    result = ValidationResult(
                        success=True,
                        reasoning=f"Test passed in {execution_time:.2f}s on attempt {attempt}/{test_case.attempts}",
                    )
                    test_case.record_result(result)
                    return result
                last_result = ValidationResult(
                    success=False,
                    reasoning=tool_call_validation.reasoning,
                    expectations_unmet=list(tool_call_validation.expectations_unmet),
                    unmet_expectation_numbers=list(tool_call_validation.unmet_expectation_numbers),
                )
                last_reason = last_result.reasoning

            if attempt < test_case.attempts and test_case.sleep_between_attempts > 0:
                time.sleep(test_case.sleep_between_attempts)

        reason = last_reason or "Test failed after all attempts"
        reason_with_attempts = f"{reason} (after {test_case.attempts} attempts)" if test_case.attempts > 1 else reason
        expectations_unmet = last_result.expectations_unmet if last_result is not None else []
        unmet_numbers = last_result.unmet_expectation_numbers if last_result is not None else []
        result = ValidationResult(
            success=False,
            reasoning=reason_with_attempts,
            expectations_unmet=expectations_unmet,
            unmet_expectation_numbers=unmet_numbers,
        )
        test_case.record_result(result)
        return result

    def case(
        self,
        query: str,
        expectations: list[str],
        *,
        expected_tool_calls: Iterable[BaseTool] | None = None,
        retry: RetryConfig | None = None,
        auto_execute: bool = True,
    ) -> ValidationResult | TestCase:
        """Build a test case and optionally execute it immediately."""
        # pylint: disable=too-many-arguments

        test_case = TestCase(
            query=query,
            expectations=expectations,
            goose=self,
            expected_tool_calls=list(expected_tool_calls) if expected_tool_calls is not None else None,
            retry=retry,
        )

        if auto_execute:
            return self.assert_case(test_case)
        return test_case

    def execute(self, test_case: TestCase) -> ValidationResult:
        """Run a test case synchronously."""

        return asyncio.run(self.run(test_case))

    def assert_case(self, test_case: TestCase) -> ValidationResult:
        """Run a test case and raise if it fails."""
        expected_tool_names = (
            [tool.name for tool in test_case.expected_tool_calls] if test_case.expected_tool_calls else []
        )

        try:
            result = self.execute(test_case)
        except Exception as exc:  # pragma: no cover - propagate but ensure execution recorded
            self._execution_history.append(
                ExecutionRecord(
                    query=test_case.query,
                    expectations=list(test_case.expectations),
                    expected_tool_calls=expected_tool_names,
                    response=test_case.last_response,
                    validation=None,
                    error=str(exc),
                )
            )
            raise

        self._execution_history.append(
            ExecutionRecord(
                query=test_case.query,
                expectations=list(test_case.expectations),
                expected_tool_calls=expected_tool_names,
                response=test_case.last_response,
                validation=result,
            )
        )

        if not result.success:
            raise AssertionError(result.reasoning or "Goose validation failed")
        return result

    def consume_execution_history(self) -> list[ExecutionRecord]:
        """Return and clear recorded execution history."""

        history = list(self._execution_history)
        self._execution_history.clear()
        return history


class TestCase:  # pylint: disable=too-many-instance-attributes
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

    async def is_valid(self) -> bool:
        """Return True when the test case succeeds."""

        if self._result is None:
            self._result = await self.goose.run(self)
        return self._result.success

    async def report(self) -> str:
        """Return the reasoning generated for this test case."""

        if self._result is None:
            self._result = await self.goose.run(self)
        return self._result.reasoning or ""
