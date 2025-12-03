"""Exceptions for test discovery and execution errors."""

from __future__ import annotations


class UnknownTestError(ValueError):
    """Raised when a requested test cannot be located."""
