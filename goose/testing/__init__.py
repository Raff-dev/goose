"""Testing framework entrypoints for Goose."""

from __future__ import annotations

from goose.testing.engine import Goose
from goose.testing.fixtures import fixture
from goose.testing.hooks import DjangoTestHooks, TestLifecycleHooks
from goose.testing.models.tests import TestDefinition, TestResult, ValidationResult
from goose.testing.test_case import TestCase

__all__ = [
    "Goose",
    "TestCase",
    "ValidationResult",
    "fixture",
    "TestLifecycleHooks",
    "DjangoTestHooks",
    "TestResult",
    "TestDefinition",
]
