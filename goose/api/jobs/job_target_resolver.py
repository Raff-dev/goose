"""Helpers for resolving execution targets for Goose jobs."""

from __future__ import annotations

from goose.api import config
from goose.api.jobs.exceptions import UnknownTestError
from goose.api.jobs.models import TestTarget
from goose.testing.discovery import load_test_definition
from goose.testing.runner import list_tests


class JobTargetResolver:
    """Resolve requested test names into concrete ``TestTarget`` objects."""

    def resolve(self, requested: list[str] | None = None) -> list[TestTarget]:
        """Return targets for all discovered tests or the requested subset."""

        return self.resolve_all() if not requested else self.resolve_specific(requested)

    def resolve_all(self) -> list[TestTarget]:
        """Return targets for every discovered test function."""

        tests = list_tests(config.get_tests_root())
        return [TestTarget.from_definition(test) for test in tests]

    def resolve_specific(self, requested: list[str]) -> list[TestTarget]:
        """Return targets for an explicit list of dotted test names."""

        targets: list[TestTarget] = []
        for qualified_name in requested:
            try:
                target = TestTarget.from_qualified_name(qualified_name)
            except ValueError as exc:
                raise UnknownTestError(f"Test name must be module-qualified: {qualified_name}") from exc

            try:
                definition = load_test_definition(target.module, target.name)
            except (AttributeError, ModuleNotFoundError, ValueError) as exc:
                raise UnknownTestError(f"Test not found: {qualified_name}") from exc

            targets.append(TestTarget.from_definition(definition))
        return targets


__all__ = ["JobTargetResolver"]
