"""Hot reload utilities for Goose modules."""

from __future__ import annotations

import importlib
import sys

from goose.core.config import GooseConfig


def collect_submodules(package_name: str) -> list[str]:
    """Find all loaded modules under a package prefix."""
    prefix = f"{package_name}."
    matches = []
    for name in sys.modules:
        if name == package_name or name.startswith(prefix):
            matches.append(name)
    return matches


def reload_module(module_name: str) -> None:
    """Reload a single module by name.

    Clears the module namespace before reload to ensure removed attributes
    (like deleted functions) are properly removed.

    If the module file was deleted, removes it from sys.modules.
    Raises import-time errors (syntax errors, missing deps) so they propagate.
    Only AttributeError/TypeError during reload are suppressed.
    """
    module = sys.modules.get(module_name)
    if module is not None:
        try:
            # Clear module namespace before reload to remove deleted attributes
            # Keep only essential module attributes that Python requires
            preserved_attrs = {
                "__name__",
                "__loader__",
                "__package__",
                "__spec__",
                "__path__",
                "__file__",
                "__cached__",
            }
            for attr in list(module.__dict__.keys()):
                if attr not in preserved_attrs:
                    delattr(module, attr)
            importlib.reload(module)
        except ModuleNotFoundError as exc:
            if exc.name == module_name:
                sys.modules.pop(module_name, None)
            else:
                raise
        except (AttributeError, TypeError):
            pass


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


def reload_source_modules(*, extra_exclude_suffixes: list[str] | None = None) -> None:
    """Reload all configured source modules and refresh the GooseApp.

    Collects modules from reload_targets, excludes those in reload_exclude,
    reloads them in dependency order, and refreshes the GooseApp instance.

    Args:
        extra_exclude_suffixes: Additional module suffixes to exclude (e.g., [".conftest"]).
    """
    config = GooseConfig()

    reload_exclude = config.compute_reload_exclude()
    extra_suffixes = extra_exclude_suffixes or []

    modules = {
        mod
        for target in config.reload_targets
        for mod in collect_submodules(target)
        if not any(mod == exc or mod.startswith(f"{exc}.") for exc in reload_exclude)
        and not any(mod.endswith(suffix) for suffix in extra_suffixes)
    }

    if modules:
        deps = _build_dependency_graph(modules)
        for module_name in _topological_sort(modules, deps):
            reload_module(module_name)

        config.refresh_app()


__all__ = ["collect_submodules", "reload_module", "reload_source_modules"]
