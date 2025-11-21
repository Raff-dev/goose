"""Enumerations describing job execution modes and statuses."""

from __future__ import annotations

from enum import Enum


class JobStatus(str, Enum):
    """Lifecycle states for an execution job."""

    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class JobMode(str, Enum):
    """Specifies how a job selects tests for execution."""

    ALL = "all"
    SELECTIVE = "selective"


__all__ = ["JobMode", "JobStatus"]
