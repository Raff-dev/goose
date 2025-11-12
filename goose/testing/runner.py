"""Test execution helpers for Goose."""

from __future__ import annotations

import time
import traceback
from pathlib import Path
from typing import Any

from goose.testing.core import Goose, TestCase
from goose.testing.discovery import discover_tests, ensure_django_ready
from goose.testing.fixtures import FIXTURE_REGISTRY, build_call_arguments
from goose.testing.types import TestDefinition, TestResult


def list_tests(start_dir: str | Path = "example_tests") -> list[TestDefinition]:
    """Return metadata for all discovered tests."""

    ensure_django_ready()
    return discover_tests(start_dir)


def run_tests(start_dir: str | Path = "example_tests") -> list[TestResult]:
    """Execute all discovered tests and return their results."""

    ensure_django_ready()
    db_state, django_active = _prepare_test_environment(setup_database=True)
    try:
        definitions = discover_tests(start_dir)
        return [_execute_test(definition) for definition in definitions]
    finally:
        _teardown_test_environment(db_state, django_active)


def _prepare_test_environment(*, setup_database: bool) -> tuple[Any | None, bool]:
    try:
        import django
        from django.test.utils import setup_databases, setup_test_environment  # type: ignore[attr-defined]
    except ImportError:  # pragma: no cover - Django not installed
        return None, False

    setup_test_environment()
    if setup_database:
        db_state = setup_databases(verbosity=0, interactive=False, keepdb=True)
    else:
        db_state = None
    return db_state, True


def _teardown_test_environment(db_state: Any | None, active: bool) -> None:
    if not active:
        return

    from django.test.utils import teardown_databases, teardown_test_environment  # type: ignore[attr-defined]

    if db_state is not None:
        teardown_databases(db_state, verbosity=0)
    teardown_test_environment()


def _execute_test(definition: TestDefinition) -> TestResult:
    start = time.time()
    fixture_cache: dict[str, Any] = {}

    try:
        FIXTURE_REGISTRY.apply_autouse(fixture_cache)
        kwargs = build_call_arguments(definition.func, fixture_cache)
        outcome = definition.func(**kwargs)
        _process_test_outcome(outcome, fixture_cache)
    except AssertionError as exc:
        duration = time.time() - start
        message = str(exc) or repr(exc)
        return TestResult(definition=definition, passed=False, duration=duration, error=message)
    except Exception:  # pragma: no cover - unexpected failure path
        duration = time.time() - start
        return TestResult(definition=definition, passed=False, duration=duration, error=traceback.format_exc())

    duration = time.time() - start
    return TestResult(definition=definition, passed=True, duration=duration)


def _process_test_outcome(outcome: Any, fixture_cache: dict[str, Any]) -> None:
    if outcome is None:
        return

    cases: list[TestCase]
    if isinstance(outcome, TestCase):
        cases = [outcome]
    elif isinstance(outcome, (list, tuple)) and all(isinstance(item, TestCase) for item in outcome):
        cases = list(outcome)
    else:
        return

    goose_instance = _extract_goose_fixture(fixture_cache)
    if goose_instance is None:
        raise AssertionError("No Goose fixture available to execute TestCase instances.")

    for case in cases:
        goose_instance.assert_case(case)


def _extract_goose_fixture(cache: dict[str, Any]) -> Goose | None:
    for candidate in ("goose", "goose_fixture"):
        value = cache.get(candidate)
        if isinstance(value, Goose):
            return value
    return None


__all__ = ["list_tests", "run_tests"]
