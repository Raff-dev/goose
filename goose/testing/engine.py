"""Execution engine that coordinates agent queries and validation."""

from __future__ import annotations

from collections.abc import Callable

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.tools import BaseTool

from goose.testing.hooks import TestLifecycleHooks
from goose.testing.models.messages import AgentResponse
from goose.testing.test_case import TestCase
from goose.testing.validator import AgentValidator


class Goose:
    """Testing helper that wraps the agent, validator, and lifecycle hooks."""

    def __init__(
        self,
        agent_query_func: Callable[[str], AgentResponse],
        *,
        hooks: TestLifecycleHooks | None = None,
        validator_model: BaseChatModel | str = "gpt-4o-mini",
    ) -> None:
        self._agent_query_func = agent_query_func
        self._validation_agent = AgentValidator(chat_model=validator_model)
        self.hooks = hooks or TestLifecycleHooks()
        self._test_case: TestCase | None = None

    def case(
        self,
        query: str,
        expectations: list[str],
        *,
        expected_tool_calls: list[BaseTool] | None = None,
    ) -> None:
        """Build a test case and execute it immediately."""

        self._test_case = TestCase(
            query_message=query,
            expectations=expectations,
            expected_tool_calls=expected_tool_calls,
        )

        try:
            response = self._agent_query_func(self._test_case.query_message)
        except Exception as exc:
            # Try to extract partial response from the exception if available
            # Some agent implementations attach partial results to exceptions
            partial_response = getattr(exc, "partial_response", None)
            if partial_response is not None:
                self._test_case.last_response = partial_response
            raise

        self._test_case.last_response = response
        self._test_case.validate_tool_calls(actual_tool_call_names=response.tool_call_names)

        evaluation = self._validation_agent.evaluate(agent_output=response, expectations=self._test_case.expectations)
        self._test_case.validate_expectations(evaluation=evaluation)

    def consume_test_case(self) -> TestCase | None:
        """
        Return the last recorded execution for the current test.
        test_case can be none if an exception was raised before case() was called.
        """

        test_case = self._test_case
        self._test_case = None
        return test_case


__all__ = ["Goose"]
