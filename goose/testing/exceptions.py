"""Exceptions for test discovery and execution errors."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from goose.testing.models.messages import AgentResponse


class UnknownTestError(ValueError):
    """Raised when a requested test cannot be located."""


class TestLoadError(Exception):
    """Raised when test code fails to load (syntax errors, missing imports, etc.)."""

    __test__ = False  # Prevent pytest from trying to collect this as a test class

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class AgentQueryError(Exception):
    """Exception that captures partial agent response on failure.

    Use this exception in your agent query function to preserve any messages
    that were collected before the error occurred. The Goose test engine will
    extract the partial_response and attach it to the test case.

    Example:
        def query(question: str) -> AgentResponse:
            collected_messages = []
            try:
                for state in agent.stream({"messages": messages}):
                    collected_messages = state.get("messages", [])
                return AgentResponse(messages=collected_messages)
            except Exception as exc:
                partial = AgentResponse(messages=collected_messages) if collected_messages else None
                raise AgentQueryError(str(exc), partial_response=partial) from exc
    """

    def __init__(self, message: str, partial_response: AgentResponse | None = None) -> None:
        super().__init__(message)
        self.partial_response = partial_response
