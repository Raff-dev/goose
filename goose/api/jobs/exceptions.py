"""Custom exceptions for Goose API job management."""

from __future__ import annotations


class UnknownTestError(ValueError):
    """Raised when a requested test cannot be located."""
