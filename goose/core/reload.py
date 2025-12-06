"""Module reload utilities for hot reload functionality."""

from __future__ import annotations

import importlib
import sys


def reload_module(module_name: str) -> None:
    """Reload a single module by name.

    If the module file was deleted, removes it from sys.modules.
    Raises import-time errors (syntax errors, missing deps) so they propagate.
    Only AttributeError/TypeError during reload are suppressed.

    Args:
        module_name: Dotted module name to reload, e.g. 'my_agent.tools'
    """
    module = sys.modules.get(module_name)
    if module is not None:
        try:
            importlib.reload(module)
        except ModuleNotFoundError as exc:
            # Only catch if the module itself is missing (file deleted).
            # If a dependency is missing, propagate the error.
            if exc.name == module_name:
                sys.modules.pop(module_name, None)
            else:
                raise
        except (AttributeError, TypeError):  # pragma: no cover - best effort
            pass


def collect_submodules(package_name: str, exclude_suffix: str | None = None) -> list[str]:
    """Find all loaded modules under a package prefix.

    Args:
        package_name: Base package name, e.g. 'my_agent'
        exclude_suffix: Optional suffix to exclude, e.g. '.conftest'

    Returns:
        List of module names under the package.
    """
    prefix = f"{package_name}."
    matches = []
    for name in sys.modules:
        if name != package_name and not name.startswith(prefix):
            continue
        if exclude_suffix and name.endswith(exclude_suffix):
            continue
        matches.append(name)
    return matches


def reload_package(package_name: str, exclude_suffix: str | None = None) -> None:
    """Reload a package and all its submodules.

    Modules are reloaded in dependency order (leaves first).

    Args:
        package_name: Base package name to reload.
        exclude_suffix: Optional suffix to exclude from reload.
    """
    submodules = collect_submodules(package_name, exclude_suffix=exclude_suffix)

    # Sort by depth (deepest first) for proper reload order
    submodules.sort(key=lambda x: x.count("."), reverse=True)

    for module_name in submodules:
        reload_module(module_name)
