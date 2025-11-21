"""Dataclasses describing job targets and metadata."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from goose.api.jobs.enums import JobStatus, TestStatus
from goose.testing.types import TestDefinition, TestResult


@dataclass(slots=True, frozen=True)
class TestTarget:
    """Lightweight identifier for a test function to execute."""

    module: str
    name: str

    @property
    def qualified_name(self) -> str:
        """Return the fully-qualified dotted name for the test."""

        return f"{self.module}.{self.name}"

    @classmethod
    def from_definition(cls, definition: TestDefinition) -> TestTarget:
        """Build a target from a discovered test definition."""

        return cls(module=definition.module, name=definition.name)

    @classmethod
    def from_qualified_name(cls, qualified_name: str) -> TestTarget:
        """Create a ``TestTarget`` by parsing a dotted qualified name."""

        if "." not in qualified_name:
            raise ValueError(f"Test name must be module-qualified: {qualified_name}")
        module, name = qualified_name.rsplit(".", 1)
        return cls(module=module, name=name)


@dataclass(slots=True)
# Dataclass captures all job metadata needed for orchestration.
# pylint: disable=too-many-instance-attributes
class Job:
    """Represents the state of a queued or executing test run."""

    id: str
    status: JobStatus
    targets: list[TestTarget]
    created_at: datetime
    updated_at: datetime
    results: list[TestResult] = field(default_factory=list)
    error: str | None = None
    test_statuses: dict[str, TestStatus] = field(default_factory=dict)


__all__ = ["Job", "TestTarget"]
