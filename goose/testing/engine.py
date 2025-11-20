"""Execution engine that coordinates agent queries and validation."""

from __future__ import annotations

import time
from collections.abc import Callable, Iterable
from typing import Any

from langchain_core.tools import BaseTool

from goose.agent_validator import AgentValidator
from goose.error_type import ErrorType
from goose.models import AgentResponse
from goose.testing.case import TestCase
from goose.testing.types import ExecutionRecord, ValidationResult


class Goose:
    """Testing helper that wraps the agent and validator logic."""

    def __init__(self, agent_query_func: Callable[[str], dict[str, Any]]):
        self._agent_query_func = agent_query_func
        self._validation_agent = AgentValidator()
        self._execution_history: list[ExecutionRecord] = []

    def case(
        self,
        query: str,
        expectations: list[str],
        *,
        expected_tool_calls: Iterable[BaseTool] | None = None,
    ) -> ValidationResult:
        """Build a test case and execute it immediately."""
        # pylint: disable=too-many-arguments

        test_case = TestCase(
            query=query,
            expectations=expectations,
            expected_tool_calls=list(expected_tool_calls) if expected_tool_calls is not None else None,
        )

        return self.assert_case(test_case)

    def assert_case(self, test_case: TestCase) -> ValidationResult:
        """Run a test case and raise if it fails."""
        expected_tool_names = self._expected_tool_names(test_case)

        try:
            result = self._execute_case(test_case)
            test_case.record_result(result)
        except Exception as exc:  # pragma: no cover - propagate but ensure execution recorded
            err_type = self._classify_exception(exc)
            self._execution_history.append(
                ExecutionRecord(
                    query=test_case.query,
                    expectations=list(test_case.expectations),
                    expected_tool_calls=expected_tool_names,
                    response=test_case.last_response,
                    validation=None,
                    error=str(exc),
                    error_type=err_type,
                )
            )
            raise

        if not result.success and result.error_type is None:
            raise RuntimeError("Failing ValidationResult missing error_type")

        self._execution_history.append(
            ExecutionRecord(
                query=test_case.query,
                expectations=list(test_case.expectations),
                expected_tool_calls=expected_tool_names,
                response=test_case.last_response,
                validation=result,
                error_type=result.error_type,
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

    def _execute_case(self, test_case: TestCase) -> ValidationResult:
        start_time = time.time()
        raw_response = self._agent_query_func(test_case.query)
        execution_time = time.time() - start_time

        response = AgentResponse.from_dict(raw_response)
        test_case.last_response = response
        evaluation = self._validation_agent.validate(response, test_case.expectations)
        unmet_numbers = list(evaluation.unmet_expectation_numbers)
        unmet_expectations = [
            test_case.expectations[index - 1] for index in unmet_numbers if 1 <= index <= len(test_case.expectations)
        ]

        if evaluation.error:
            return ValidationResult(
                success=False,
                reasoning=evaluation.reasoning,
                expectations_unmet=unmet_expectations,
                unmet_expectation_numbers=unmet_numbers,
                error_type=ErrorType.EXPECTATION,
            )

        tool_call_validation = test_case.validate_tool_calls(response)
        if tool_call_validation.success:
            result = ValidationResult(
                success=True,
                reasoning=f"Test passed in {execution_time:.2f}s",
            )
            return result

        return ValidationResult(
            success=False,
            reasoning=tool_call_validation.reasoning,
            expectations_unmet=list(tool_call_validation.expectations_unmet),
            unmet_expectation_numbers=list(tool_call_validation.unmet_expectation_numbers),
            error_type=ErrorType.TOOL_CALL,
        )

    @staticmethod
    def _classify_exception(exc: Exception) -> ErrorType:
        return ErrorType.VALIDATION if isinstance(exc, AssertionError) else ErrorType.UNEXPECTED

    @staticmethod
    def _expected_tool_names(test_case: TestCase) -> list[str]:
        if not test_case.expected_tool_calls:
            return []
        return [tool.name for tool in test_case.expected_tool_calls]


__all__ = ["Goose"]
