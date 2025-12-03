"""Test execution helpers for Goose."""

from __future__ import annotations

import time
from typing import Any

from goose.testing.discovery import load_from_qualified_name
from goose.testing.fixtures import apply_autouse, build_call_arguments, extract_goose_fixture
from goose.testing.models.tests import TestDefinition, TestResult


def execute_test(definition: TestDefinition) -> TestResult:
    """Execute a single Goose test with fixtures and hooks.

    Args:
        definition: The test definition to run.

    Returns:
        The result of the test execution, including pass/fail status and metadata.
    """
    refreshed_definitions = load_from_qualified_name(definition.qualified_name)
    if refreshed_definitions:
        definition = refreshed_definitions[0]

    start = time.time()
    fixture_cache: dict[str, Any] = {}

    kwargs = build_call_arguments(definition.func, fixture_cache)
    goose_instance = extract_goose_fixture(fixture_cache)
    goose_instance.hooks.pre_test(definition)

    apply_autouse(fixture_cache)

    exception = _execute(definition, kwargs)
    goose_instance.hooks.post_test(definition)

    duration = time.time() - start
    test_case = goose_instance.consume_test_case()

    return TestResult(definition=definition, duration=duration, test_case=test_case, exception=exception)


def _execute(definition: TestDefinition, kwargs: dict[str, Any]) -> Exception | None:
    """Execute the test function and return pass/fail status."""
    try:
        definition.func(**kwargs)
        return None
    except Exception as exc:  # pylint: disable=broad-except
        return exc


__all__ = ["execute_test"]
