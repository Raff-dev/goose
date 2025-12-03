"""Discovery utilities for Goose tests."""

from __future__ import annotations

import importlib
import inspect
import pkgutil
import sys
from pathlib import Path
from types import ModuleType

from goose.api import config as api_config
from goose.testing import fixtures as fixture_registry
from goose.testing.exceptions import UnknownTestError
from goose.testing.models.tests import TestDefinition

MODULE_PREFIXES = ["test_", "tests_"]
FUNCTION_PREFIXES = ["test_"]


def _is_test_module(name: str) -> bool:
    """Return True if *name* looks like a test module."""
    leaf = name.rsplit(".", 1)[-1]
    return any(leaf.startswith(prefix) for prefix in MODULE_PREFIXES)


def _collect_functions(module: ModuleType):
    """Yield TestDefinitions for test functions defined in *module*."""
    for name in dir(module):
        if not any(name.startswith(prefix) for prefix in FUNCTION_PREFIXES):
            continue
        attr = getattr(module, name)
        if inspect.isfunction(attr) and attr.__module__ == module.__name__:
            yield TestDefinition(module=module.__name__, name=name, func=attr)


def _ensure_test_import_paths() -> Path:
    """Ensure the configured tests root and its parent are importable."""
    tests_path = api_config.get_tests_root()
    for candidate in (tests_path, tests_path.parent):
        candidate_path = str(candidate)
        if candidate_path not in sys.path:
            sys.path.insert(0, candidate_path)
    return tests_path


def _refresh_test_modules(root_package: str) -> None:
    """Reload all test modules under root_package so file changes are picked up.

    Excludes conftest modules as they are handled separately to ensure
    proper fixture registration order.
    """
    prefix = f"{root_package}."
    test_modules = [
        name
        for name in sys.modules
        if (name == root_package or name.startswith(prefix)) and not name.endswith(".conftest")
    ]
    for module_name in test_modules:
        module = sys.modules.get(module_name)
        if module is not None:
            try:
                importlib.reload(module)
            except (ImportError, AttributeError, TypeError):  # pragma: no cover - best effort reload
                pass


def _import_conftest(qualified_name: str) -> None:
    """Import conftest.py from the target package to register fixtures.

    Clears the fixture registry, refreshes all test modules, and reloads the
    conftest module to ensure fixtures are always freshly registered.
    """
    root_package = qualified_name.split(".")[0]
    fixture_registry.reset_registry()
    _refresh_test_modules(root_package)
    conftest_name = f"{root_package}.conftest"
    try:
        if conftest_name in sys.modules:
            importlib.reload(sys.modules[conftest_name])
        else:
            importlib.import_module(conftest_name)
    except ModuleNotFoundError:
        pass


def _try_as_package(qualified_name: str) -> list[TestDefinition] | None:
    """Try to resolve *qualified_name* as a package containing test modules."""
    try:
        package = importlib.import_module(qualified_name)
        return [
            defn
            for _, module_name, _ in pkgutil.walk_packages(package.__path__, package.__name__ + ".")
            if _is_test_module(module_name)
            for defn in _collect_functions(importlib.import_module(module_name))
        ]
    except (ImportError, AttributeError):
        return None


def _try_as_module(qualified_name: str) -> list[TestDefinition] | None:
    """Try to resolve *qualified_name* as a module containing test functions."""
    try:
        module = importlib.import_module(qualified_name)
        definitions = list(_collect_functions(module))
        return definitions or None
    except ImportError:
        return None


def _try_as_function(qualified_name: str) -> list[TestDefinition] | None:
    """Try to resolve *qualified_name* as a module.function reference."""
    parts = qualified_name.split(".")
    if len(parts) < 2:
        return None
    module_name = ".".join(parts[:-1])
    func_name = parts[-1]
    try:
        module = importlib.import_module(module_name)
        attr = getattr(module, func_name)
        if inspect.isfunction(attr) and attr.__module__ == module.__name__:
            return [TestDefinition(module=module.__name__, name=func_name, func=attr)]
    except (ImportError, AttributeError):
        pass
    return None


def load_from_qualified_name(qualified_name: str) -> list[TestDefinition]:
    """Resolve *qualified_name* into one or more test definitions.

    Accepts a dotted Python identifier and attempts resolution in order:
        1. Package - walk all ``test_*`` / ``tests_*`` modules recursively
        2. Module  - collect test functions from the module itself
        3. Function - return single ``module.function`` reference

    Assumptions:
        - ``goose.api.config.get_tests_root()`` points to a valid test directory.
        - The target package/module is importable after ``sys.path`` is adjusted.
        - Test functions are top-level, named ``test_*`` or ``tests_*``.

    Side effects (every call):
        - Resets the fixture registry, discarding previously registered fixtures.
        - Re-imports ``<root_package>.conftest`` to re-register fixtures.
        - Re-imports target modules; changes on disk are picked up.

    Note:
        Calling this function multiple times with the same input is safe but
        will repeat all side effects. The fixture registry is always cleared,
        so only fixtures from the most recent call remain active.

    Args:
        qualified_name: Dotted target, e.g. ``"my_tests"``, ``"my_tests.test_foo"``,
            or ``"my_tests.test_foo.test_some_case"``.

    Returns:
        A list of ``TestDefinition`` objects for the discovered tests.

    Raises:
        ValueError: If *qualified_name* cannot be resolved to any tests.
    """
    _ensure_test_import_paths()
    _import_conftest(qualified_name)

    for resolver in (_try_as_package, _try_as_module, _try_as_function):
        result = resolver(qualified_name)
        if result is not None:
            return result

    raise UnknownTestError(f"Could not resolve qualified name: {qualified_name!r}")


__all__ = ["load_from_qualified_name"]
