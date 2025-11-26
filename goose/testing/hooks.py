"""Lifecycle hook abstractions for Goose tests."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from goose.testing.models.tests import TestDefinition


class TestLifecycleHooks:
    """Suite and per-test lifecycle hooks invoked around Goose executions."""

    def pre_test(self, definition: TestDefinition) -> None:  # pylint: disable=unused-argument
        """Hook invoked before a single test executes."""

    def post_test(self, definition: TestDefinition) -> None:  # pylint: disable=unused-argument
        """Hook invoked after a single test completes."""


class DjangoTestHooks(TestLifecycleHooks):
    """Lifecycle hooks that configure Django's test environment."""

    def __init__(self) -> None:
        self._db_state: Iterable[tuple[Any, str, bool]] | None = None
        self._active = False

    def pre_test(self, definition: TestDefinition) -> None:  # pylint: disable=unused-argument
        from django.test.utils import (  # type: ignore[attr-defined]  # pylint: disable=import-outside-toplevel
            setup_databases,
            setup_test_environment,
        )

        if self._active:
            return

        setup_test_environment()
        self._db_state = setup_databases(verbosity=0, interactive=False, keepdb=True)
        self._active = True

    def post_test(self, definition: TestDefinition) -> None:  # pylint: disable=unused-argument
        from django.core.management import call_command  # pylint: disable=import-outside-toplevel
        from django.test.utils import (  # pylint: disable=import-outside-toplevel
            teardown_databases,
            teardown_test_environment,
        )

        if not self._active:
            return

        if self._db_state is None:
            return

        # Flush all data to ensure clean state for next test
        call_command("flush", verbosity=0, interactive=False)
        teardown_databases(self._db_state, verbosity=0, keepdb=True)
        self._db_state = None
        teardown_test_environment()
        self._active = False


__all__ = ["TestLifecycleHooks", "DjangoTestHooks"]
