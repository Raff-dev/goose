"""Shared data structures for Goose testing."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from goose.testing.error_type import ErrorType
from goose.testing.models import AgentResponse


@dataclass(slots=True)
class TestDefinition:
    """Metadata about an individual test function."""

    module: str
    name: str
    func: Callable[..., Any]

    @property
    def qualified_name(self) -> str:
        """Return the fully-qualified name of the test function."""

        return f"{self.module}.{self.name}"


@dataclass(slots=True)
class ValidationResult:
    """Validator outcome for a single agent execution."""

    success: bool
    reasoning: str = ""
    expectations_unmet: list[str] = field(default_factory=list)
    unmet_expectation_numbers: list[int] = field(default_factory=list)
    error_type: ErrorType | None = None


@dataclass(slots=True)
class TestResult:
    """Outcome from executing a Goose test."""

    definition: TestDefinition
    passed: bool
    duration: float
    error: str | None = None
    error_type: ErrorType | None = None
    execution: ExecutionRecord | None = None

    @property
    def name(self) -> str:
        """Return the fully-qualified name for the result's definition."""

        return self.definition.qualified_name


@dataclass(slots=True)
class ExecutionRecord:
    """Captures a single agent execution during a test."""

    query: str
    expectations: list[str]
    expected_tool_calls: list[str]
    response: AgentResponse | None
    validation: ValidationResult | None = None
    exception: Exception | None = None

    @property
    def error(self) -> str | None:
        """Return the error message from validation or exception."""

        if self.validation and not self.validation.success:
            return self.validation.reasoning
        if self.exception:
            return str(self.exception)
        return None

    @property
    def error_type(self) -> ErrorType | None:
        """Return the error type from validation or exception."""

        if self.validation and not self.validation.success:
            return self.validation.error_type
        if self.exception:
            if isinstance(self.exception, AssertionError):
                return ErrorType.VALIDATION
            return ErrorType.UNEXPECTED
        return None


__all__ = ["TestDefinition", "ValidationResult", "TestResult", "ExecutionRecord"]
