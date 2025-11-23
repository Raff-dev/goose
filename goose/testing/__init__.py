"""Testing framework entrypoints for Goose."""

from __future__ import annotations

from goose.testing.case import TestCase
from goose.testing.engine import Goose
from goose.testing.fixtures import fixture
from goose.testing.runner import (
    BaseTestRunner,
    DjangoTestRunner,
    get_test_runner,
    run_single_test,
    run_tests,
    set_test_runner,
)
from goose.testing.types import ExecutionRecord, TestDefinition, TestResult, ValidationResult

__all__ = [
    "Goose",
    "TestCase",
    "ValidationResult",
    "fixture",
    "BaseTestRunner",
    "DjangoTestRunner",
    "get_test_runner",
    "run_single_test",
    "run_tests",
    "set_test_runner",
    "TestResult",
    "TestDefinition",
    "ExecutionRecord",
]
