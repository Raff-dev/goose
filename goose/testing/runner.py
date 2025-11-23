"""Test execution helpers for Goose."""

from __future__ import annotations

import time
import traceback
from collections.abc import Iterator
from typing import Any

from goose.testing.engine import Goose
from goose.testing.fixtures import FIXTURE_REGISTRY, build_call_arguments
from goose.testing.types import ExecutionRecord, TestDefinition, TestResult


class BaseTestRunner:
    """Base runner that exposes setup/teardown hooks."""

    def __init__(self) -> None:
        self._active_depth = 0
        self._active = False

    def setup(self) -> None:  # pylint: disable=unused-argument
        pass

    def teardown(self) -> None:  # pylint: disable=unused-argument
        pass

    def run_suite(self, definitions: list[TestDefinition]) -> Iterator[TestResult]:
        self.setup()
        try:
            for definition in definitions:
                yield _execute_test(definition)
        finally:
            self.teardown()

    def run_single(self, definition: TestDefinition) -> TestResult:
        self.setup()
        try:
            return _execute_test(definition)
        finally:
            self.teardown()


class DjangoTestRunner(BaseTestRunner):
    """Runner that configures Django's test environment when available."""

    def __init__(self) -> None:
        super().__init__()
        self._db_state: Any | None = None

    def setup(self) -> None:
        from django.test.utils import setup_databases, setup_test_environment  # noqa

        setup_test_environment()
        self._db_state = setup_databases(verbosity=0, interactive=False, keepdb=True)
        self._active = True

    def teardown(self) -> None:
        from django.test.utils import teardown_databases, teardown_test_environment  # noqa

        if not self._active:
            return

        teardown_databases(self._db_state, verbosity=0, keepdb=True)
        teardown_test_environment()



def _execute_test(definition: TestDefinition) -> TestResult:
    start = time.time()
    fixture_cache: dict[str, Any] = {}
    execution: ExecutionRecord | None = None

    try:
        FIXTURE_REGISTRY.apply_autouse(fixture_cache)
        kwargs = build_call_arguments(definition.func, fixture_cache)

        # run the test here
        definition.func(**kwargs)

        execution = _get_execution(fixture_cache)
    except AssertionError as exc:

        duration = time.time() - start
        execution = _get_execution(fixture_cache)
        return TestResult(
            definition=definition,
            passed=False,
            duration=duration,
            error=str(exc),
            error_type=execution.error_type,
            execution=execution,
        )
    except Exception:  # pylint: disable=broad-exception-caught

        duration = time.time() - start
        execution = _get_execution(fixture_cache)
        return TestResult(
            definition=definition,
            passed=False,
            duration=duration,
            error=traceback.format_exc(),
            error_type=execution.error_type,
            execution=execution,
        )

    duration = time.time() - start
    execution = _get_execution(fixture_cache)
    return TestResult(
        definition=definition,
        passed=True,
        duration=duration,
        execution=execution
    )



def _extract_goose_fixture(cache: dict[str, Any]) -> Goose:
    for candidate in ("goose", "goose_fixture"):
        value = cache.get(candidate)
        if hasattr(value, "get_execution"):
            return value

    raise AssertionError("No Goose fixture available to retrieve execution history.")


def _get_execution(cache: dict[str, Any]) -> ExecutionRecord:
    goose_instance = _extract_goose_fixture(cache)
    return goose_instance.get_execution()




__all__ = [
    "BaseTestRunner",
    "DjangoTestRunner",
]
