"""Shared data structures for Goose testing."""

from __future__ import annotations

import traceback
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from goose.testing.errors import ErrorType, ExpectationValidationError, ToolCallValidationError
from goose.testing.test_case import TestCase


@dataclass(slots=True)
class TestDefinition:
    """Metadata about an individual test function."""

    __test__ = False

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

    __test__ = False

    success: bool
    reasoning: str = ""
    expectations_unmet: list[str] = field(default_factory=list)
    unmet_expectation_numbers: list[int] = field(default_factory=list)
    failure_reasons: dict[str, str] = field(default_factory=dict)
    error_type: ErrorType | None = None


# pylint: disable=too-many-instance-attributes
@dataclass(slots=True)
class TestResult:
    """Outcome from executing a Goose test."""

    __test__ = False

    definition: TestDefinition
    duration: float
    test_case: TestCase | None = None
    exception: Exception | None = None
    error_message: str | None = None
    error_type: ErrorType | None = None
    expectations_unmet: list[str] = field(default_factory=list)
    failure_reasons: dict[str, str] = field(default_factory=dict)

    @property
    def total_tokens(self) -> int:
        """Return total tokens used in this test's agent response."""
        if self.test_case is None or self.test_case.last_response is None:
            return 0
        return self.test_case.last_response.token_usage.total_tokens

    def __post_init__(self) -> None:
        """Compute derived fields based on the exception."""
        if self.exception is None:
            self.error_message = None
            self.error_type = None
            self.expectations_unmet = []
            self.failure_reasons = {}

        elif isinstance(self.exception, ToolCallValidationError):
            self.error_message = str(self.exception)
            self.error_type = ErrorType.TOOL_CALL
            self.expectations_unmet = []
            self.failure_reasons = {}

        elif isinstance(self.exception, ExpectationValidationError):
            self.error_message = self.exception.reasoning
            self.error_type = ErrorType.EXPECTATION
            self.expectations_unmet = self.exception.expectations_unmet
            self.failure_reasons = self.exception.failure_reasons

        elif isinstance(self.exception, AssertionError):
            formatted = "".join(
                traceback.format_exception(type(self.exception), self.exception, self.exception.__traceback__)
            )
            self.error_message = formatted
            self.error_type = ErrorType.VALIDATION
            self.expectations_unmet = []
            self.failure_reasons = {}

        else:
            self.error_message = "".join(
                traceback.format_exception(type(self.exception), self.exception, self.exception.__traceback__)
            )
            self.error_type = ErrorType.UNEXPECTED
            self.expectations_unmet = []
            self.failure_reasons = {}

    @property
    def name(self) -> str:
        """Return the fully-qualified name for the result's definition."""
        return self.definition.qualified_name

    @property
    def passed(self) -> bool:
        """Return whether the test passed validation."""
        return self.exception is None


__all__ = ["TestDefinition", "ValidationResult", "TestResult", "TestCase"]
