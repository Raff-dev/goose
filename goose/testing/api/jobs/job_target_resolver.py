"""Helpers for resolving execution targets for Goose jobs."""

from __future__ import annotations

from goose.core.config import GooseConfig
from goose.testing.discovery import load_from_qualified_name
from goose.testing.models.tests import TestDefinition


def resolve_targets(requested: list[str] | None = None) -> list[TestDefinition]:
    """Return test definitions for all tests or the requested dotted names."""

    if not requested:
        return load_from_qualified_name(GooseConfig.TESTS_MODULE)

    targets: list[TestDefinition] = []
    for qualified_name in requested:
        definitions = load_from_qualified_name(qualified_name)
        targets.extend(definitions)
    return targets


__all__ = ["resolve_targets"]
