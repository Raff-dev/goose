"""Shared data structures for Goose testing."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from goose.error_type import ErrorType
from goose.models import AgentResponse


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
    executions: list[ExecutionRecord] = field(default_factory=list)

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
    error: str | None = None
    # Backend-supplied explicit classification of the failure (if any)
    error_type: ErrorType | None = None


__all__ = ["TestDefinition", "ValidationResult", "TestResult", "ExecutionRecord"]
