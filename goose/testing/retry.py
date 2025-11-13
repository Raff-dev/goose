"""Retry configuration for Goose test execution."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class RetryConfig:
    """Configuration for retrying flaky agent validations."""

    attempts: int = 1
    sleep_between_attempts: float = 0.0


__all__ = ["RetryConfig"]
