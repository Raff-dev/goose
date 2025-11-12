"""Shared data structures for Goose testing."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from collections.abc import Callable


@dataclass(slots=True)
class TestDefinition:
    """Metadata about an individual test function."""

    module: str
    name: str
    func: Callable[..., Any]

    @property
    def qualified_name(self) -> str:
        return f"{self.module}.{self.name}"


@dataclass(slots=True)
class TestResult:
    """Outcome from executing a Goose test."""

    definition: TestDefinition
    passed: bool
    duration: float
    error: str | None = None

    @property
    def name(self) -> str:
        return self.definition.qualified_name


__all__ = ["TestDefinition", "TestResult"]
