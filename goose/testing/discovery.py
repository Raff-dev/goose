"""Discovery utilities for Goose tests."""

# Pylint note: this module does a lot of branching to support partial reloads.
# The resulting helper functions naturally return early, so we silence the
# "too-many-return-statements" warning at the module level.
# pylint: disable=too-many-return-statements

from __future__ import annotations

import importlib
import inspect
import pkgutil
import sys
from pathlib import Path
from types import ModuleType

from goose.testing import fixtures as fixture_registry
from goose.testing.imports import ensure_test_import_paths
from goose.testing.models.tests import TestDefinition

_LIBRARY_ROOT = Path(__file__).resolve().parents[1]
_SKIPPED_TOP_LEVEL_DIRS = {".venv", "venv", ".git", "node_modules", ".direnv"}


def discover_tests(start_dir: Path) -> list[TestDefinition]:
    """Import test modules beneath *start_dir* and collect Goose tests."""

    test_root = ensure_test_import_paths(target_path=start_dir)
    _purge_project_modules(test_root.parent)
    fixture_registry.reset_registry()
    importlib.invalidate_caches()
    _import_fixture_modules(test_root)

    definitions: list[TestDefinition] = []
    for module_path in sorted(test_root.rglob("test_*.py")):
        module_name = _module_name_from_path(module_path, test_root)
        if module_name is None:
            continue

        module = _import_or_reload_module(module_name)
        definitions.extend(_collect_module_definitions(module))

    return definitions


def load_from_qualified_name(qualified_name: str, *, tests_root: Path | None = None) -> list[TestDefinition]:
    """Resolve *qualified_name* into one or more test definitions."""

    prepared_root = _prepare_import_context(tests_root)

    direct_definition = _resolve_direct_target(qualified_name, prepared_root)
    if direct_definition is not None:
        return [direct_definition]

    modules = _load_module_hierarchy(qualified_name, prepared_root)
    definitions: list[TestDefinition] = []
    for current in modules:
        definitions.extend(_collect_module_definitions(current))

    return definitions


def _prepare_import_context(tests_root: Path | None) -> Path:
    """Ensure sys.path and caches are ready for importing tests."""

    target_path = tests_root or Path.cwd()
    prepared_root = ensure_test_import_paths(target_path=target_path)
    if tests_root is not None:
        _purge_project_modules(prepared_root.parent)
    fixture_registry.reset_registry()
    importlib.invalidate_caches()
    return prepared_root


def _resolve_direct_target(qualified_name: str, prepared_root: Path) -> TestDefinition | None:
    """Return a specific test function if *qualified_name* points to one."""

    if "." not in qualified_name:
        return None

    module_name, attr_name = qualified_name.rsplit(".", 1)
    if not module_name or not attr_name:
        return None

    try:
        module = _import_module_with_fixtures(module_name, prepared_root)
    except (ImportError, ModuleNotFoundError, ValueError):
        return None

    func = getattr(module, attr_name, None)
    if not inspect.isfunction(func):
        return None

    return TestDefinition(module=module.__name__, name=attr_name, func=func)


def _load_module_hierarchy(module_name: str, prepared_root: Path) -> list[ModuleType]:
    """Import *module_name* and any nested modules beneath it."""

    try:
        module = _import_module_with_fixtures(module_name, prepared_root)
    except ModuleNotFoundError as exc:
        msg = f"Test target not found: {module_name}. " "Targets must be dotted modules or module.function names."
        raise ValueError(msg) from exc

    modules: list[ModuleType] = [module]
    if hasattr(module, "__path__"):
        prefix = f"{module.__name__}."
        for module_info in pkgutil.walk_packages(module.__path__, prefix):
            modules.append(importlib.import_module(module_info.name))
    return modules


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
        _import_or_reload_module(module_name)


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


def _import_module_with_fixtures(module_name: str, test_root: Path) -> ModuleType:
    """Import *module_name* and ensure its fixtures are loaded."""

    ensure_test_import_paths(target_path=test_root)
    module = _import_or_reload_module(module_name)
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


def _purge_project_modules(project_root: Path) -> None:
    """Remove cached modules that live inside *project_root*."""

    resolved_root = project_root.resolve()
    library_root = _LIBRARY_ROOT
    modules_to_clear: list[str] = []

    for name, module in list(sys.modules.items()):
        module_file = getattr(module, "__file__", None)
        if module_file is None:
            continue
        try:
            module_path = Path(module_file).resolve()
        except (OSError, RuntimeError):
            continue
        if _should_skip_module(module_path, resolved_root, library_root):
            continue
        modules_to_clear.append(name)

    for name in modules_to_clear:
        sys.modules.pop(name, None)


def _should_skip_module(module_path: Path, project_root: Path, library_root: Path) -> bool:
    """Return True when *module_path* should not be purged."""

    if not _path_within(module_path, project_root):
        return True
    if _path_within(module_path, library_root):
        return True

    try:
        relative = module_path.relative_to(project_root)
    except ValueError:
        return True

    if not relative.parts:
        return True

    top_level = relative.parts[0]
    if top_level in _SKIPPED_TOP_LEVEL_DIRS:
        return True
    if "site-packages" in relative.parts:
        return True

    return False


def _path_within(candidate: Path, root: Path) -> bool:
    """Return True when *candidate* is inside *root*."""

    try:
        candidate.relative_to(root)
    except ValueError:
        return False
    return True


def _import_or_reload_module(module_name: str) -> ModuleType:
    """Import *module_name*, reloading it if already cached."""

    if module_name in sys.modules:
        cached_names = [name for name in sys.modules if name == module_name or name.startswith(f"{module_name}.")]
        for name in cached_names:
            sys.modules.pop(name, None)

    importlib.invalidate_caches()
    return importlib.import_module(module_name)


__all__ = ["discover_tests", "load_from_qualified_name"]
