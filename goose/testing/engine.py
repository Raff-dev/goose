"""Execution engine that coordinates agent queries and validation."""

from __future__ import annotations

import time
from collections.abc import Callable, Iterable
from typing import Any

from langchain_core.tools import BaseTool

from goose.testing.case import TestCase
from goose.testing.error_type import ErrorType
from goose.testing.models import AgentResponse
from goose.testing.runner import BaseTestRunner
from goose.testing.types import ExecutionRecord, ValidationResult
from goose.testing.validator import AgentValidator


class Goose:
    """Testing helper that wraps the agent, validator, and runner logic."""

    def __init__(
        self,
        agent_query_func: Callable[[str], dict[str, Any]],
        *,
        test_runner: BaseTestRunner = BaseTestRunner(),
    ) -> None:
        self._agent_query_func = agent_query_func
        self._validation_agent = AgentValidator()
        self._execution: ExecutionRecord | None = None
        self.runner = test_runner

    def case(
        self,
        query: str,
        expectations: list[str],
        *,
        expected_tool_calls: list[BaseTool] | None = None,
    ) -> ValidationResult:
        """Build a test case and execute it immediately."""

        test_case = TestCase(
            query=query,
            expectations=expectations,
            expected_tool_calls=expected_tool_calls,
        )

        try:
            result = self._execute_case(test_case)
        except Exception as exc:  # pragma: no cover - propagate but ensure execution recorded
            self._record_execution(test_case=test_case, result=None, exc=exc)
            raise

        self._record_execution(test_case=test_case, result=result, exc=None)

        if not result.success:
            raise AssertionError(result.reasoning or "Goose validation failed")

        return result

    def _record_execution(self, test_case: TestCase, result: ValidationResult | None, exc: Exception | None) -> None:
        """Record an execution in the history log."""
        self._execution = ExecutionRecord(
            query=test_case.query,
            expectations=list(test_case.expectations),
            expected_tool_calls=test_case.expected_tool_names,
            response=test_case.last_response,
            validation=result,
            exception=exc,
        )

    def consume_execution_history(self) -> ExecutionRecord | None:
        """Return and clear recorded execution history."""

        execution = self._execution
        self._execution = None
        return execution

    def get_execution(self) -> ExecutionRecord | None:
        """Compatibility shim for legacy runner helpers."""

        return self.consume_execution_history()

    def _execute_case(self, test_case: TestCase) -> ValidationResult:
        """Run a single test case and return the validation result."""

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



__all__ = ["Goose"]
