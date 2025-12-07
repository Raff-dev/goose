"""Tests for GooseApp loader utilities."""

from __future__ import annotations

import sys

import pytest

from goose.core.app import GooseApp
from goose.core.loader import get_app, get_effective_reload_targets, load_app


class TestLoadApp:
    """Tests for load_app function."""

    def test_invalid_format_no_colon(self) -> None:
        """Raises ValueError if path has no colon separator."""
        with pytest.raises(ValueError, match="Invalid app_path format"):
            load_app("gooseapp.app")

    def test_invalid_format_empty_var(self) -> None:
        """Handles edge case of empty variable name."""
        with pytest.raises(ValueError, match="Invalid app_path format"):
            load_app("gooseapp.app:")

    def test_module_not_found(self) -> None:
        """Raises ImportError if module doesn't exist."""
        with pytest.raises(ImportError):
            load_app("nonexistent.module:app")

    def test_attribute_not_found(self, tmp_path, monkeypatch) -> None:
        """Raises AttributeError if variable doesn't exist in module."""
        # Create a temporary module
        module_dir = tmp_path / "test_pkg"
        module_dir.mkdir()
        (module_dir / "__init__.py").write_text("")
        (module_dir / "app.py").write_text("other_var = 'not an app'")

        monkeypatch.syspath_prepend(str(tmp_path))

        with pytest.raises(AttributeError):
            load_app("test_pkg.app:app")

    def test_wrong_type(self, tmp_path, monkeypatch) -> None:
        """Raises TypeError if variable is not a GooseApp."""
        # Create a temporary module with wrong type
        module_dir = tmp_path / "test_pkg2"
        module_dir.mkdir()
        (module_dir / "__init__.py").write_text("")
        (module_dir / "app.py").write_text("app = 'not a GooseApp'")

        monkeypatch.syspath_prepend(str(tmp_path))

        with pytest.raises(TypeError, match="Expected GooseApp"):
            load_app("test_pkg2.app:app")

    def test_loads_valid_app(self, tmp_path, monkeypatch) -> None:
        """Successfully loads a valid GooseApp."""
        # Create a temporary module with valid GooseApp
        module_dir = tmp_path / "test_pkg3"
        module_dir.mkdir()
        (module_dir / "__init__.py").write_text("")
        (module_dir / "app.py").write_text(
            "from goose.core.app import GooseApp\n" "app = GooseApp(reload_targets=['my_agent'])\n"
        )

        monkeypatch.syspath_prepend(str(tmp_path))

        result = load_app("test_pkg3.app:app")

        assert isinstance(result, GooseApp)
        assert result.reload_targets == ["my_agent"]


class TestGetApp:
    """Tests for get_app function."""

    def test_invalid_format(self) -> None:
        """Raises ValueError if path has no colon separator."""
        with pytest.raises(ValueError, match="Invalid app_path format"):
            get_app("gooseapp.app")

    def test_uses_cached_module(self, tmp_path, monkeypatch) -> None:
        """Uses already imported module from sys.modules."""
        # Create a temporary module
        module_dir = tmp_path / "test_pkg4"
        module_dir.mkdir()
        (module_dir / "__init__.py").write_text("")
        (module_dir / "app.py").write_text("from goose.core.app import GooseApp\n" "app = GooseApp()\n")

        monkeypatch.syspath_prepend(str(tmp_path))

        # First call imports the module
        result1 = get_app("test_pkg4.app:app")

        # Verify it's in sys.modules
        assert "test_pkg4.app" in sys.modules

        # Second call should use cached module
        result2 = get_app("test_pkg4.app:app")

        # Both should be the same instance (from cached module)
        assert result1 is result2


class TestGetEffectiveReloadTargets:
    """Tests for get_effective_reload_targets function."""

    def test_invalid_format(self) -> None:
        """Raises ValueError if path has no colon separator."""
        with pytest.raises(ValueError, match="Invalid app_path format"):
            get_effective_reload_targets("gooseapp.app")

    def test_includes_base_module(self, tmp_path, monkeypatch) -> None:
        """Always includes the gooseapp base module."""
        # Create a temporary module
        module_dir = tmp_path / "mygooseapp"
        module_dir.mkdir()
        (module_dir / "__init__.py").write_text("")
        (module_dir / "app.py").write_text("from goose.core.app import GooseApp\n" "app = GooseApp()\n")

        monkeypatch.syspath_prepend(str(tmp_path))

        result = get_effective_reload_targets("mygooseapp.app:app")

        assert "mygooseapp" in result

    def test_includes_app_reload_targets(self, tmp_path, monkeypatch) -> None:
        """Includes reload targets from GooseApp."""
        module_dir = tmp_path / "mygooseapp2"
        module_dir.mkdir()
        (module_dir / "__init__.py").write_text("")
        (module_dir / "app.py").write_text(
            "from goose.core.app import GooseApp\n" "app = GooseApp(reload_targets=['my_agent', 'utils'])\n"
        )

        monkeypatch.syspath_prepend(str(tmp_path))

        result = get_effective_reload_targets("mygooseapp2.app:app")

        assert "my_agent" in result
        assert "utils" in result
        assert "mygooseapp2" in result

    def test_includes_explicit_targets(self, tmp_path, monkeypatch) -> None:
        """Includes explicit CLI targets."""
        module_dir = tmp_path / "mygooseapp3"
        module_dir.mkdir()
        (module_dir / "__init__.py").write_text("")
        (module_dir / "app.py").write_text(
            "from goose.core.app import GooseApp\n" "app = GooseApp(reload_targets=['my_agent'])\n"
        )

        monkeypatch.syspath_prepend(str(tmp_path))

        result = get_effective_reload_targets(
            "mygooseapp3.app:app",
            explicit_targets=["extra_module"],
        )

        assert "my_agent" in result
        assert "extra_module" in result
        assert "mygooseapp3" in result

    def test_deduplicates_targets(self, tmp_path, monkeypatch) -> None:
        """Doesn't duplicate targets if specified multiple times."""
        module_dir = tmp_path / "mygooseapp4"
        module_dir.mkdir()
        (module_dir / "__init__.py").write_text("")
        (module_dir / "app.py").write_text(
            "from goose.core.app import GooseApp\n" "app = GooseApp(reload_targets=['my_agent', 'mygooseapp4'])\n"
        )

        monkeypatch.syspath_prepend(str(tmp_path))

        result = get_effective_reload_targets(
            "mygooseapp4.app:app",
            explicit_targets=["my_agent"],
        )

        # Count occurrences - should only appear once each
        assert result.count("my_agent") == 1
        assert result.count("mygooseapp4") == 1
