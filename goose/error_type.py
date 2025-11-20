"""Shared ErrorType enum used across backend modules.

Defines a stable set of failure classifications that the backend will
return to the frontend. Using a dedicated module avoids circular
imports between validator, testing, and schema modules.
"""

from __future__ import annotations

from enum import Enum


class ErrorType(str, Enum):
    """Stable classification labels for Goose test failures."""

    EXPECTATION = "expectation"
    VALIDATION = "validation"
    TOOL_CALL = "tool_call"
    UNEXPECTED = "unexpected"
