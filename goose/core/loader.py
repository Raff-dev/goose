"""Loader utilities for GooseApp."""

from __future__ import annotations

import importlib
import os
import sys

from goose.core.app import GooseApp


def _ensure_cwd_in_path() -> None:
    """Ensure current working directory is in sys.path for imports."""
    cwd = os.getcwd()
    if cwd not in sys.path:
        sys.path.insert(0, cwd)


def load_app(app_path: str):
    """Load GooseApp from 'module:var' path.

    Args:
        app_path: Path in format 'module.path:variable_name'
                  e.g., 'gooseapp.app:app'

    Returns:
        The GooseApp instance.

    Raises:
        ValueError: If app_path format is invalid.
        ImportError: If module cannot be imported.
        AttributeError: If variable doesn't exist in module.
    """
    _ensure_cwd_in_path()

    if ":" not in app_path:
        raise ValueError(f"Invalid app_path format: {app_path!r}. Expected 'module:variable'")

    module_path, var_name = app_path.rsplit(":", 1)

    if not module_path or not var_name:
        raise ValueError(f"Invalid app_path format: {app_path!r}. Expected 'module:variable'")

    module = importlib.import_module(module_path)
    app = getattr(module, var_name)

    if not isinstance(app, GooseApp):
        raise TypeError(f"Expected GooseApp instance, got {type(app).__name__}")

    return app


def get_app(app_path: str):
    """Get the current GooseApp instance (fresh after reload).

    Unlike load_app, this fetches from sys.modules if already imported,
    ensuring we get the latest version after a reload.

    Args:
        app_path: Path in format 'module.path:variable_name'

    Returns:
        The GooseApp instance.
    """
    if ":" not in app_path:
        raise ValueError(f"Invalid app_path format: {app_path!r}. Expected 'module:variable'")

    module_path, var_name = app_path.rsplit(":", 1)

    # Try to get from sys.modules first (already imported/reloaded)
    module = sys.modules.get(module_path)
    if module is None:
        module = importlib.import_module(module_path)

    app = getattr(module, var_name)

    if not isinstance(app, GooseApp):
        raise TypeError(f"Expected GooseApp instance, got {type(app).__name__}")

    return app


def get_effective_reload_targets(app_path: str, explicit_targets: list[str] | None = None):
    """Get reload targets including the app module itself.

    The gooseapp module is always included to ensure tools are refreshed
    when the app.py file changes.

    Args:
        app_path: Path in format 'module.path:variable_name'
        explicit_targets: Additional explicit reload targets (e.g., from CLI).

    Returns:
        List of module names to reload.
    """
    if ":" not in app_path:
        raise ValueError(f"Invalid app_path format: {app_path!r}. Expected 'module:variable'")

    # Extract the base module (e.g., "gooseapp" from "gooseapp.app:app")
    module_path = app_path.rsplit(":", 1)[0]
    base_module = module_path.split(".")[0]

    # Load the app to get its configured reload_targets
    app = get_app(app_path)

    # Combine all targets
    targets = set(app.reload_targets)

    # Add explicit CLI targets
    if explicit_targets:
        targets.update(explicit_targets)

    # Always include the gooseapp base module
    targets.add(base_module)

    return list(targets)
