"""Helpers for resolving execution targets for Goose jobs."""

from __future__ import annotations

from goose.api import config
from goose.api.jobs.exceptions import UnknownTestError
from goose.testing.discovery import discover_tests, load_test_definition
from goose.testing.types import TestDefinition


def resolve_targets(requested: list[str] | None = None) -> list[TestDefinition]:
    """Return test definitions for all tests or the requested dotted names."""

    if not requested:
        return discover_tests(config.get_tests_root())

    targets: list[TestDefinition] = []
    for qualified_name in requested:
        try:
            module, name = qualified_name.rsplit(".", 1)
        except ValueError as exc:
            raise UnknownTestError(f"Test name must be module-qualified: {qualified_name}") from exc

        try:
            definition = load_test_definition(module, name)
        except (AttributeError, ModuleNotFoundError, ValueError) as exc:
            raise UnknownTestError(f"Test not found: {qualified_name}") from exc

        targets.append(definition)
    return targets


__all__ = ["resolve_targets"]
