"""Testing framework entrypoints for Goose."""

from __future__ import annotations

from goose.testing.case import TestCase
from goose.testing.engine import Goose
from goose.testing.fixtures import fixture
from goose.testing.runner import list_tests, run_single_test, run_tests
from goose.testing.types import ExecutionRecord, TestDefinition, TestResult, ValidationResult

__all__ = [
    "Goose",
    "TestCase",
    "ValidationResult",
    "fixture",
    "list_tests",
    "run_single_test",
    "run_tests",
    "TestResult",
    "TestDefinition",
    "ExecutionRecord",
]
