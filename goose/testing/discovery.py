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


def _reload_module(module_name: str) -> None:
    """Reload a single module by name, ignoring errors."""
    module = sys.modules.get(module_name)
    if module is not None:
        try:
            importlib.reload(module)
        except (ImportError, AttributeError, TypeError):  # pragma: no cover - best effort
            pass


def _collect_submodules(package_name: str, *, exclude_suffix: str | None = None) -> list[str]:
    """Find all loaded modules under a package prefix."""
    prefix = f"{package_name}."
    matches = []
    for name in sys.modules:
        if name != package_name and not name.startswith(prefix):
            continue
        if exclude_suffix and name.endswith(exclude_suffix):
            continue
        matches.append(name)
    return matches


def _build_dependency_graph(modules: set[str]) -> dict[str, set[str]]:
    """Build a mapping of module -> modules it imports from (within the set)."""
    deps: dict[str, set[str]] = {}
    for module_name in modules:
        module = sys.modules.get(module_name)
        if module is None:
            deps[module_name] = set()
            continue
        imported_from = set()
        for name in dir(module):
            attr = getattr(module, name, None)
            attr_module = getattr(attr, "__module__", None)
            if attr_module and attr_module != module_name and attr_module in modules:
                imported_from.add(attr_module)
        deps[module_name] = imported_from
    return deps


def _topological_sort(modules: set[str], deps: dict[str, set[str]]) -> list[str]:
    """Sort modules so dependencies come before dependents."""
    reloaded: set[str] = set()
    reload_order: list[str] = []

    while len(reloaded) < len(modules):
        progress = False
        for module_name in modules:
            if module_name in reloaded:
                continue
            if deps[module_name] <= reloaded:
                reload_order.append(module_name)
                reloaded.add(module_name)
                progress = True
        if not progress:
            # Circular dependency - add remaining in any order
            reload_order.extend(m for m in modules if m not in reloaded)
            break

    return reload_order


def _reload_test_modules(root_package: str) -> None:
    """Reload all test modules under root_package so file changes are picked up."""
    for module_name in _collect_submodules(root_package, exclude_suffix=".conftest"):
        _reload_module(module_name)


def _reload_conftest(root_package: str) -> None:
    """Import or reload conftest.py from the target package to register fixtures."""
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
    """
    root_package = qualified_name.split(".")[0]

    _ensure_test_import_paths()

    # Reload configured source targets in dependency order
    modules = {mod for target in api_config.get_reload_targets() for mod in _collect_submodules(target)}

    if modules:
        deps = _build_dependency_graph(modules)
        for module_name in _topological_sort(modules, deps):
            _reload_module(module_name)

    fixture_registry.reset_registry()
    _reload_conftest(root_package)
    _reload_test_modules(root_package)

    for resolver in (_try_as_package, _try_as_module, _try_as_function):
        result = resolver(qualified_name)
        if result is not None:
            return result

    raise UnknownTestError(f"Could not resolve qualified name: {qualified_name!r}")


__all__ = ["load_from_qualified_name"]
