"""Dataclasses describing job targets and metadata."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from goose.testing.api.jobs.enums import JobStatus, TestStatus
from goose.testing.models.tests import TestDefinition, TestResult


@dataclass(slots=True)
# Dataclass captures all job metadata needed for orchestration.
# pylint: disable=too-many-instance-attributes
class Job:
    """Represents the state of a queued or executing test run."""

    id: str
    status: JobStatus
    targets: list[TestDefinition]
    created_at: datetime
    updated_at: datetime
    results: list[TestResult] = field(default_factory=list)
    error: str | None = None
    test_statuses: dict[str, TestStatus] = field(default_factory=dict)


__all__ = ["Job"]
