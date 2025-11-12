"""Shared data structures for Goose testing."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from goose.agent_validator import ValidationResult
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
class TestResult:
    """Outcome from executing a Goose test."""

    definition: TestDefinition
    passed: bool
    duration: float
    error: str | None = None
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


__all__ = ["TestDefinition", "TestResult", "ExecutionRecord"]
