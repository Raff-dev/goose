"""Enumerations describing job execution modes and statuses."""

from __future__ import annotations

from enum import Enum


class JobStatus(str, Enum):
    """Lifecycle states for an execution job."""

    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class TestStatus(str, Enum):
    """Per-test lifecycle states reported to clients."""

    __test__ = False

    QUEUED = "queued"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"


__all__ = ["JobStatus", "TestStatus"]
