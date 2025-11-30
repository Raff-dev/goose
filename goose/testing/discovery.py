"""Discovery utilities for Goose tests."""

from __future__ import annotations

import importlib
import inspect
import pkgutil
from pathlib import Path
from types import ModuleType

from goose.testing.imports import ensure_test_import_paths
from goose.testing.models.tests import TestDefinition


def discover_tests(start_dir: Path) -> list[TestDefinition]:
    """Import test modules beneath *start_dir* and collect Goose tests."""

    test_root = ensure_test_import_paths(target_path=start_dir)
    _import_fixture_modules(test_root)

    definitions: list[TestDefinition] = []
    for module_path in sorted(test_root.rglob("test_*.py")):
        module_name = _module_name_from_path(module_path, test_root)
        if module_name is None:
            continue

        module = importlib.import_module(module_name)
        definitions.extend(_collect_module_definitions(module))

    return definitions


def load_from_qualified_name(qualified_name: str) -> list[TestDefinition]:
    """Resolve *qualified_name* into one or more test definitions."""

    if "." in qualified_name:
        module_name, attr_name = qualified_name.rsplit(".", 1)
        if module_name and attr_name:
            try:
                module = _import_module_with_fixtures(module_name)
            except (ImportError, ModuleNotFoundError, ValueError):
                pass
            else:
                func = getattr(module, attr_name, None)
                if inspect.isfunction(func):
                    definition = TestDefinition(module=module.__name__, name=attr_name, func=func)
                    return [definition]

    try:
        module = _import_module_with_fixtures(qualified_name)
    except ModuleNotFoundError as exc:
        msg = f"Test target not found: {qualified_name}. " "Targets must be dotted modules or module.function names."
        raise ValueError(msg) from exc
    modules: list[ModuleType] = [module]

    if hasattr(module, "__path__"):
        prefix = f"{module.__name__}."
        for module_info in pkgutil.walk_packages(module.__path__, prefix):
            modules.append(importlib.import_module(module_info.name))

    definitions: list[TestDefinition] = []
    for current in modules:
        definitions.extend(_collect_module_definitions(current))

    return definitions


def _collect_module_definitions(module: ModuleType) -> list[TestDefinition]:
    """Return Goose test definitions declared inside *module*."""

    if not hasattr(module, "__dict__"):
        return []

    definitions: list[TestDefinition] = []

    for name, value in module.__dict__.items():
        if not name.startswith("test_"):
            continue
        if not inspect.isfunction(value):
            continue
        if value.__module__ != module.__name__:
            continue
        definitions.append(TestDefinition(module=module.__name__, name=name, func=value))

    return definitions


def _import_fixture_modules(test_root: Path) -> None:
    """Import all ``conftest`` modules under *test_root*."""

    for fixture_path in sorted(test_root.rglob("conftest.py")):
        module_name = _module_name_from_path(fixture_path, test_root)
        if module_name is None:
            continue
        importlib.import_module(module_name)


def _module_name_from_path(module_path: Path, test_root: Path) -> str | None:
    """Return dotted module name for *module_path* relative to *test_root*."""

    resolved_root = test_root.parent
    resolved_path = module_path.resolve().with_suffix("")

    try:
        relative = resolved_path.relative_to(resolved_root)
    except ValueError:
        return None

    parts = relative.parts
    if not parts:
        return None

    for part in parts:
        if part.startswith("."):
            return None

    return ".".join(parts)


def _import_module_with_fixtures(module_name: str) -> ModuleType:
    """Import *module_name* and ensure its fixtures are loaded."""

    ensure_test_import_paths(target_path=Path.cwd())
    module = importlib.import_module(module_name)
    module_file = getattr(module, "__file__", None)

    if module_file is not None:
        current = Path(module_file).resolve()
        if current.is_file():
            current = current.parent

        top_level = module.__name__.split(".", 1)[0]
        found_top_level = current.name == top_level
        while not found_top_level:
            parent = current.parent
            if parent == current:
                break
            current = parent
            found_top_level = current.name == top_level

        if found_top_level:
            _import_fixture_modules(current)

    return module


__all__ = ["discover_tests", "load_from_qualified_name"]
