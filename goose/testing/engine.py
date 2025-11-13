"""Execution engine that coordinates agent queries and validation."""

from __future__ import annotations

import time
from collections.abc import Callable, Iterable
from typing import Any

from langchain_core.tools import BaseTool

from goose.agent_validator import AgentValidator, ValidationResult
from goose.models import AgentResponse
from goose.testing.case import TestCase
from goose.testing.retry import RetryConfig
from goose.testing.types import ExecutionRecord


class Goose:
    """Testing helper that wraps the agent and validator logic."""

    def __init__(self, agent_query_func: Callable[[str], dict[str, Any]]):
        self._agent_query_func = agent_query_func
        self._validation_agent = AgentValidator()
        self._execution_history: list[ExecutionRecord] = []

    def run(self, test_case: TestCase) -> ValidationResult:  # pylint: disable=too-many-locals
        """Execute a test case and return its validation result."""

        last_reason: str | None = None
        last_result: ValidationResult | None = None
        for attempt in range(1, test_case.attempts + 1):
            start_time = time.time()
            raw_response = self._agent_query_func(test_case.query)
            execution_time = time.time() - start_time

            response = AgentResponse.from_dict(raw_response)
            test_case.last_response = response
            evaluation = self._validation_agent.validate(response, test_case.expectations)
            unmet_numbers = list(evaluation.unmet_expectation_numbers)
            unmet_expectations = [
                test_case.expectations[index - 1]
                for index in unmet_numbers
                if 1 <= index <= len(test_case.expectations)
            ]

            if evaluation.error:
                last_result = ValidationResult(
                    success=False,
                    reasoning=evaluation.reasoning,
                    expectations_unmet=unmet_expectations,
                    unmet_expectation_numbers=unmet_numbers,
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
    ) -> ValidationResult:
        """Build a test case and execute it immediately."""
        # pylint: disable=too-many-arguments

        test_case = self.build_case(
            query=query,
            expectations=expectations,
            expected_tool_calls=expected_tool_calls,
            retry=retry,
        )

        return self.assert_case(test_case)

    def build_case(
        self,
        *,
        query: str,
        expectations: list[str],
        expected_tool_calls: Iterable[BaseTool] | None = None,
        retry: RetryConfig | None = None,
    ) -> TestCase:
        """Construct a test case without executing it."""

        return TestCase(
            query=query,
            expectations=expectations,
            expected_tool_calls=list(expected_tool_calls) if expected_tool_calls is not None else None,
            retry=retry,
        )

    def assert_case(self, test_case: TestCase) -> ValidationResult:
        """Run a test case and raise if it fails."""
        expected_tool_names = (
            [tool.name for tool in test_case.expected_tool_calls] if test_case.expected_tool_calls else []
        )

        try:
            result = self.run(test_case)
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


__all__ = ["Goose"]
