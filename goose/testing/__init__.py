"""Testing framework entrypoints for Goose."""

from __future__ import annotations

from goose.agent_validator import ValidationResult

from goose.testing.core import Goose, RetryConfig, TestCase
from goose.testing.fixtures import fixture
from goose.testing.runner import list_tests, run_tests
from goose.testing.types import TestDefinition, TestResult

__all__ = [
    "Goose",
    "RetryConfig",
    "TestCase",
    "ValidationResult",
    "fixture",
    "list_tests",
    "run_tests",
    "TestResult",
    "TestDefinition",
]
