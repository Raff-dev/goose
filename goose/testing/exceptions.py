"""Exceptions for test discovery and execution errors."""

from __future__ import annotations


class UnknownTestError(ValueError):
    """Raised when a requested test cannot be located."""


class TestLoadError(Exception):
    """Raised when test code fails to load (syntax errors, missing imports, etc.)."""

    __test__ = False  # Prevent pytest from trying to collect this as a test class

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)
