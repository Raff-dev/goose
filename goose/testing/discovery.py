"""Discovery utilities for Goose tests."""

from __future__ import annotations

import importlib
import inspect
import os
import pkgutil
import sys
from pathlib import Path
from types import ModuleType

from goose.core.config import GooseConfig
from goose.core.reload import collect_submodules, reload_module, reload_source_modules
from goose.testing import fixtures as fixture_registry
from goose.testing.exceptions import TestLoadError, UnknownTestError
from goose.testing.models.tests import TestDefinition

MODULE_PREFIXES = ["test_", "tests_"]
FUNCTION_PREFIXES = ["test_"]


def _is_test_module(name: str) -> bool:
    """Return True if *name* looks like a test module."""
    leaf = name.rsplit(".", 1)[-1]
    return any(leaf.startswith(prefix) for prefix in MODULE_PREFIXES)


def _collect_functions(module: ModuleType):
    """Yield TestDefinitions for test functions defined in *module*, ordered by line number."""
    functions = []
    for name in dir(module):
        if not any(name.startswith(prefix) for prefix in FUNCTION_PREFIXES):
            continue
        attr = getattr(module, name)
        if inspect.isfunction(attr) and attr.__module__ == module.__name__:
            functions.append((attr.__code__.co_firstlineno, name, attr))

    # Sort by line number to preserve source order
    functions.sort(key=lambda x: x[0])

    for _lineno, name, func in functions:
        yield TestDefinition(module=module.__name__, name=name, func=func)


def _ensure_test_import_paths() -> Path:
    """Ensure necessary paths are importable for test discovery.

    Adds the current working directory and the parent of tests_dir to sys.path.
    This allows importing project modules (e.g., gooseapp) and test modules.
    """
    config = GooseConfig()
    tests_path = config.tests_dir

    # Ensure cwd is in path (for importing project modules like gooseapp)
    cwd = os.getcwd()
    if cwd not in sys.path:
        sys.path.insert(0, cwd)

    # Also add parent of tests_dir for test discovery
    # (needed when tests_dir is a nested directory like tmp_path/sample_suite)
    parent_path = str(tests_path.parent)
    if parent_path not in sys.path:
        sys.path.insert(0, parent_path)

    return tests_path


def _collect_submodules_with_exclude(package_name: str, *, exclude_suffix: str | None = None) -> list[str]:
    """Find all loaded modules under a package prefix, with optional suffix exclusion."""
    modules = collect_submodules(package_name)
    if exclude_suffix:
        modules = [m for m in modules if not m.endswith(exclude_suffix)]
    return modules


def _try_as_package(qualified_name: str) -> list[TestDefinition] | None:
    """Try to resolve *qualified_name* as a package containing test modules.

    Returns None if qualified_name is not a package.
    Raises ModuleNotFoundError if the package doesn't exist.
    Raises other import errors (syntax errors, missing deps) from test modules.
    """
    package = importlib.import_module(qualified_name)

    if not hasattr(package, "__path__"):
        return None

    return [
        defn
        for _, module_name, _ in pkgutil.walk_packages(package.__path__, package.__name__ + ".")
        if _is_test_module(module_name)
        for defn in _collect_functions(importlib.import_module(module_name))
    ]


def _try_as_module(qualified_name: str) -> list[TestDefinition] | None:
    """Try to resolve *qualified_name* as a module containing test functions.

    Returns None if no test functions found.
    Raises ModuleNotFoundError if the module doesn't exist.
    Raises other import errors (syntax errors, missing deps).
    """
    module = importlib.import_module(qualified_name)
    definitions = list(_collect_functions(module))
    return definitions or None


def _try_as_function(qualified_name: str) -> list[TestDefinition] | None:
    """Try to resolve *qualified_name* as a module.function reference.

    Returns None if function not found or not a test function.
    Raises ModuleNotFoundError if the module doesn't exist.
    Raises other import errors (syntax errors, missing deps).
    """
    parts = qualified_name.split(".")
    if len(parts) < 2:
        return None
    module_name = ".".join(parts[:-1])
    func_name = parts[-1]

    module = importlib.import_module(module_name)

    attr = getattr(module, func_name, None)
    if attr is not None and inspect.isfunction(attr) and attr.__module__ == module.__name__:
        return [TestDefinition(module=module.__name__, name=func_name, func=attr)]
    return None


def load_from_qualified_name(qualified_name: str) -> list[TestDefinition]:
    """Resolve *qualified_name* into one or more test definitions.

    Accepts a dotted Python identifier and attempts resolution in order:
        1. Package - walk all ``test_*`` / ``tests_*`` modules recursively
        2. Module  - collect test functions from the module itself
        3. Function - return single ``module.function`` reference

    Assumptions:
        - The target package/module is importable (cwd is in sys.path).
        - Test functions are top-level, named ``test_*`` or ``tests_*``.

    Side effects (every call):
        - Reloads configured source targets (agent, tools, etc.)
        - Resets the fixture registry, discarding previously registered fixtures.
        - Re-imports ``<root_package>.conftest`` to re-register fixtures.
        - Refreshes test modules so file changes are picked up.

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
        UnknownTestError: If *qualified_name* cannot be resolved to any tests.
        TestLoadError: If test code fails to load (syntax errors, missing imports, etc.).
    """
    try:
        return _load_from_qualified_name(qualified_name)
    except UnknownTestError:
        raise
    except Exception as exc:
        raise TestLoadError("Failed to load tests") from exc


def _load_from_qualified_name(qualified_name: str) -> list[TestDefinition]:
    """Internal implementation of load_from_qualified_name."""
    root_package = qualified_name.split(".")[0]

    _ensure_test_import_paths()

    config = GooseConfig()

    # Clear fixture registry before reloading any modules
    # (conftest modules will re-register fixtures when reloaded)
    fixture_registry.reset_registry()

    # Reload configured source targets in dependency order
    # Exclude conftest modules (handled separately below)
    reload_source_modules(extra_exclude_suffixes=[".conftest"])

    # Refresh the GooseApp instance after hot reload (if configured)
    # This ensures tools and other config are updated
    config.refresh_app()

    # Import or reload conftest.py to register fixtures (required)
    conftest_name = f"{root_package}.conftest"
    if conftest_name in sys.modules:
        importlib.reload(sys.modules[conftest_name])
    else:
        importlib.import_module(conftest_name)

    # Reload test modules so file changes are picked up
    for module_name in _collect_submodules_with_exclude(root_package, exclude_suffix=".conftest"):
        reload_module(module_name)

    # Attempt resolution strategies in order
    for resolver in (_try_as_package, _try_as_module, _try_as_function):
        try:
            result = resolver(qualified_name)
            if result is not None:
                return result
        except ModuleNotFoundError as exc:
            # Only continue if the target module itself is not found.
            # If a dependency is missing, propagate the error.
            if exc.name and qualified_name.startswith(exc.name):
                continue
            raise

    raise UnknownTestError(f"Could not resolve qualified name: {qualified_name!r}")


__all__ = ["load_from_qualified_name"]
