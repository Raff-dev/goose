"""Test execution helpers for Goose."""

from __future__ import annotations

import time
import traceback
from typing import Any

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
    passed = True
    error_message: str | None = None

    apply_autouse(fixture_cache)
    kwargs = build_call_arguments(definition.func, fixture_cache)
    goose_instance = extract_goose_fixture(fixture_cache)
    goose_instance.hooks.pre_test(definition)

    try:
        definition.func(**kwargs)
    except AssertionError as exc:
        passed = False
        error_message = str(exc)
    except Exception:  # pylint: disable=broad-exception-caught
        passed = False
        error_message = traceback.format_exc()

    duration = time.time() - start
    execution = goose_instance.get_execution()
    result = TestResult(
        definition=definition,
        passed=passed,
        duration=duration,
        error=error_message,
        error_type=execution.error_type,
        execution=execution,
    )

    goose_instance.hooks.post_test(definition, result)
    return result


__all__ = ["execute_test"]
