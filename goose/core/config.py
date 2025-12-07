"""Configuration for the Goose API server.

Uses convention over configuration with a fixed gooseapp/ structure:

    gooseapp/
    ├── __init__.py
    ├── app.py          # Must export `app = GooseApp(...)`
    ├── conftest.py     # Test fixtures
    └── tests/
        └── test_*.py   # Test files
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

from goose.core.loader import get_app, load_app

if TYPE_CHECKING:
    from goose.core.app import GooseApp


class GooseConfig:
    """Singleton configuration for the Goose API server.

    All paths are derived from the fixed gooseapp/ convention.
    """

    _instance: GooseConfig | None = None
    _initialized: bool

    # Fixed conventions
    GOOSEAPP_DIR = "gooseapp"
    APP_MODULE = "gooseapp.app"
    APP_VARIABLE = "app"
    TESTS_MODULE = "gooseapp.tests"
    CONFTEST_MODULE = "gooseapp.conftest"

    def __new__(cls) -> GooseConfig:
        if cls._instance is None:
            instance = super().__new__(cls)
            instance._initialized = False
            instance._base_path = Path.cwd()
            instance._goose_app = None
            instance._reload_targets = []
            cls._instance = instance
        return cls._instance

    def __init__(self) -> None:
        # All initialization done in __new__
        pass

    @classmethod
    def reset(cls) -> None:
        """Reset the singleton instance (for testing)."""
        cls._instance = None

    @property
    def base_path(self) -> Path:
        """Base path for the project (cwd by default)."""
        return self._base_path

    @base_path.setter
    def base_path(self, path: Path) -> None:
        self._base_path = path

    @property
    def gooseapp_dir(self) -> Path:
        """Path to the gooseapp directory."""
        return self._base_path / self.GOOSEAPP_DIR

    @property
    def tests_dir(self) -> Path:
        """Path to the tests directory."""
        return self.gooseapp_dir / "tests"

    @property
    def goose_app(self) -> GooseApp | None:
        """The loaded GooseApp instance."""
        return self._goose_app

    @goose_app.setter
    def goose_app(self, app: GooseApp | None) -> None:
        self._goose_app = app

    @property
    def reload_targets(self) -> list[str]:
        """Modules to reload before test runs."""
        return self._reload_targets

    @reload_targets.setter
    def reload_targets(self, targets: list[str]) -> None:
        self._reload_targets = list(targets)

    def exists(self) -> bool:
        """Check if gooseapp directory exists."""
        return self.gooseapp_dir.exists()

    def validate(self) -> list[str]:
        """Validate the gooseapp structure.

        Returns:
            List of error messages, empty if valid.
        """
        errors = []

        if not self.gooseapp_dir.exists():
            errors.append(f"Directory not found: {self.gooseapp_dir}")
            return errors

        app_file = self.gooseapp_dir / "app.py"
        if not app_file.exists():
            errors.append(f"Missing app file: {app_file}")

        if not self.tests_dir.exists():
            errors.append(f"Missing tests directory: {self.tests_dir}")

        return errors

    def load_app(self) -> GooseApp:
        """Load the GooseApp from gooseapp/app.py.

        Returns:
            The loaded GooseApp instance.

        Raises:
            ImportError: If the module cannot be imported.
            AttributeError: If 'app' is not found in the module.
        """
        # Ensure base_path is in sys.path for imports
        path_str = str(self._base_path)
        if path_str not in sys.path:
            sys.path.insert(0, path_str)

        app_path = f"{self.APP_MODULE}:{self.APP_VARIABLE}"
        self._goose_app = load_app(app_path)
        return self._goose_app  # type: ignore[return-value]

    def refresh_app(self) -> GooseApp | None:
        """Reload the GooseApp after hot reload.

        Only refreshes if the gooseapp module was previously imported.
        This prevents overriding manually-set apps (e.g., in tests).

        Returns:
            The fresh GooseApp instance, or None if gooseapp is not available.
        """
        # Only refresh if gooseapp was previously loaded
        # This prevents overriding test fixtures that set config.goose_app directly
        if self.APP_MODULE not in sys.modules:
            return self._goose_app

        app_path = f"{self.APP_MODULE}:{self.APP_VARIABLE}"
        try:
            self._goose_app = get_app(app_path)
        except (ImportError, ModuleNotFoundError, AttributeError):
            # gooseapp module or variable doesn't exist
            pass
        return self._goose_app

    def compute_reload_targets(self) -> list[str]:
        """Compute the list of modules to reload before test runs.

        Combines:
        1. GooseApp.reload_targets
        2. Always includes 'gooseapp' for hot reload

        Returns:
            Deduplicated list of module names to reload.
        """
        targets = {self.GOOSEAPP_DIR}

        if self._goose_app:
            targets.update(self._goose_app.reload_targets)

        return sorted(targets)

    def compute_reload_exclude(self) -> list[str]:
        """Compute the list of module prefixes to exclude from reloading.

        Returns:
            List of module name prefixes to skip during reload.
        """
        if self._goose_app:
            return list(self._goose_app.reload_exclude)
        return []
