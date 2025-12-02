"""Helpers for resolving execution targets for Goose jobs."""

from __future__ import annotations

from goose.api import config
from goose.api.jobs.exceptions import UnknownTestError
from goose.testing.discovery import discover_tests, load_from_qualified_name
from goose.testing.models.tests import TestDefinition


def resolve_targets(requested: list[str] | None = None) -> list[TestDefinition]:
    """Return test definitions for all tests or the requested dotted names."""

    tests_root = config.get_tests_root()
    if not requested:
        return discover_tests(tests_root)

    targets: list[TestDefinition] = []
    for qualified_name in requested:
        try:
            definitions = load_from_qualified_name(qualified_name, tests_root=tests_root)
        except (AttributeError, ModuleNotFoundError, ValueError) as exc:
            raise UnknownTestError(f"Test not found: {qualified_name}") from exc

        targets.extend(definitions)
    return targets


__all__ = ["resolve_targets"]
