"""Shared ErrorType enum used across testing and API modules."""

from __future__ import annotations

from enum import Enum


class ErrorType(str, Enum):
    """Stable classification labels for Goose test failures."""

    EXPECTATION = "expectation"
    VALIDATION = "validation"
    TOOL_CALL = "tool_call"
    UNEXPECTED = "unexpected"
