"""Lifecycle hook abstractions for Goose tests."""

from __future__ import annotations

from typing import Any

from goose.testing.types import TestDefinition, TestResult


class TestLifecycleHooks:
    """Suite and per-test lifecycle hooks invoked around Goose executions."""

    def pre_test(self, definition: TestDefinition) -> None:  # pylint: disable=unused-argument
        """Hook invoked before a single test executes."""

    def post_test(self, definition: TestDefinition, result: TestResult) -> None:  # pylint: disable=unused-argument
        """Hook invoked after a single test completes."""


class DjangoTestHooks(TestLifecycleHooks):
    """Lifecycle hooks that configure Django's test environment."""

    def __init__(self) -> None:
        self._db_state: Any | None = None
        self._active = False

    def pre_test(self, definition: TestDefinition) -> None:  # pylint: disable=unused-argument
        from django.test.utils import setup_databases, setup_test_environment  # pylint: disable=import-outside-toplevel

        setup_test_environment()
        self._db_state = setup_databases(verbosity=0, interactive=False, keepdb=True)
        self._active = True

    def post_test(self, definition: TestDefinition, result: TestResult) -> None:  # pylint: disable=unused-argument
        from django.test.utils import (  # pylint: disable=import-outside-toplevel
            teardown_databases,
            teardown_test_environment,
        )

        if not self._active:
            return

        teardown_databases(self._db_state, verbosity=0, keepdb=True)
        self._db_state = None
        teardown_test_environment()
        self._active = False


__all__ = ["TestLifecycleHooks", "DjangoTestHooks"]
