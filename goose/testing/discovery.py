"""Discovery utilities for Goose tests."""

from __future__ import annotations

import importlib
import inspect
from pathlib import Path

from goose.testing.imports import ensure_test_import_paths
from goose.testing.types import TestDefinition


def discover_tests(start_dir: Path) -> list[TestDefinition]:
    """Import modules beneath *start_dir* and collect test functions."""

    test_root = ensure_test_import_paths(target_path=start_dir)
    fixture_modules = sorted(test_root.rglob("conftest.py"))
    test_modules = sorted(test_root.rglob("test_*.py"))
    module_paths = fixture_modules + test_modules

    definitions: list[TestDefinition] = []

    for module_path in module_paths:
        resolved = module_path.resolve()
        if test_root not in resolved.parents and resolved != test_root:
            continue

        module_name = ".".join(resolved.with_suffix("").relative_to(test_root).parts)
        module = importlib.import_module(module_name)

        for name, value in module.__dict__.items():
            if not name.startswith("test_"):
                continue
            if not inspect.isfunction(value):
                continue
            if value.__module__ != module.__name__:
                continue
            definitions.append(TestDefinition(module=module.__name__, name=name, func=value))

    return definitions


def load_test_definition(module_name: str, function_name: str) -> TestDefinition:
    """Load a single test function by module and function name."""

    test_root = Path.cwd()
    ensure_test_import_paths(target_path=test_root)

    module = importlib.import_module(module_name)
    func = getattr(module, function_name)

    if not inspect.isfunction(func):  # pragma: no cover - defensive guard
        raise ValueError(f"{module_name}.{function_name} is not a test function")

    return TestDefinition(module=module.__name__, name=function_name, func=func)


__all__ = ["discover_tests", "load_test_definition"]
