"""Test execution helpers for Goose."""

from __future__ import annotations

import time
import traceback
from typing import Any

from goose.testing.error_type import ErrorType
from goose.testing.fixtures import apply_autouse, build_call_arguments, extract_goose_fixture
from goose.testing.types import TestDefinition, TestResult


def execute_test(definition: TestDefinition) -> TestResult:
    """Execute a single Goose test with fixtures and hooks.

    Args:
        definition: The test definition to run.

    Returns:
        The result of the test execution, including pass/fail status and metadata.
    """
    start = time.time()
    fixture_cache: dict[str, Any] = {}

    kwargs = build_call_arguments(definition.func, fixture_cache)
    goose_instance = extract_goose_fixture(fixture_cache)
    goose_instance.hooks.pre_test(definition)

    apply_autouse(fixture_cache)

    passed, error_message = _execute(definition, kwargs)
    goose_instance.hooks.post_test(definition)

    duration = time.time() - start
    execution = goose_instance.get_execution()

    if execution is None:
        # this happens when an exception is raised before Goose.case is called
        return TestResult(
            definition=definition,
            passed=passed,
            duration=duration,
            error=error_message,
            error_type=ErrorType.UNEXPECTED,
            execution=None,
        )

    return TestResult(
        definition=definition,
        passed=passed,
        duration=duration,
        error=error_message,
        error_type=execution.error_type,
        execution=execution,
    )


def _execute(definition: TestDefinition, kwargs: dict[str, Any]) -> tuple[bool, str | None]:
    """Execute the test function and return pass/fail status."""
    try:
        definition.func(**kwargs)
        return True, None
    except AssertionError as exc:
        return False, str(exc)
    except Exception:  # pylint: disable=broad-except
        return False, traceback.format_exc()


__all__ = ["execute_test"]
