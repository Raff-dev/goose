"""Tests for API config module."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest

from goose.core.app import GooseApp
from goose.core.config import GooseConfig


@pytest.fixture(autouse=True)
def reset_config() -> Iterator[None]:
    """Reset the GooseConfig singleton before each test."""
    GooseConfig.reset()
    yield
    GooseConfig.reset()


class TestGooseConfig:
    """Tests for GooseConfig singleton class."""

    def test_is_singleton(self) -> None:
        """GooseConfig is a singleton."""
        config1 = GooseConfig()
        config2 = GooseConfig()
        assert config1 is config2

    def test_reset_creates_new_instance(self) -> None:
        """reset() creates a new singleton instance."""
        config1 = GooseConfig()
        GooseConfig.reset()
        config2 = GooseConfig()
        assert config1 is not config2

    def test_default_paths(self, tmp_path: Path) -> None:
        """GooseConfig has correct default paths."""
        config = GooseConfig()
        config.base_path = tmp_path
        assert config.gooseapp_dir == tmp_path / "gooseapp"
        assert config.tests_dir == tmp_path / "gooseapp" / "tests"

    def test_class_constants(self) -> None:
        """GooseConfig has correct class constants."""
        assert GooseConfig.GOOSEAPP_DIR == "gooseapp"
        assert GooseConfig.APP_MODULE == "gooseapp.app"
        assert GooseConfig.APP_VARIABLE == "app"
        assert GooseConfig.TESTS_MODULE == "gooseapp.tests"
        assert GooseConfig.CONFTEST_MODULE == "gooseapp.conftest"

    def test_exists_false_when_no_gooseapp(self, tmp_path: Path) -> None:
        """exists() returns False when gooseapp/ doesn't exist."""
        config = GooseConfig()
        config.base_path = tmp_path
        assert config.exists() is False

    def test_exists_true_when_gooseapp_exists(self, tmp_path: Path) -> None:
        """exists() returns True when gooseapp/ exists."""
        (tmp_path / "gooseapp").mkdir()
        config = GooseConfig()
        config.base_path = tmp_path
        assert config.exists() is True

    def test_validate_missing_gooseapp(self, tmp_path: Path) -> None:
        """validate() returns errors when gooseapp/ missing."""
        config = GooseConfig()
        config.base_path = tmp_path
        errors = config.validate()
        assert len(errors) == 1
        assert "not found" in errors[0]

    def test_validate_missing_app_and_tests(self, tmp_path: Path) -> None:
        """validate() returns errors for missing app.py and tests/."""
        gooseapp_dir = tmp_path / "gooseapp"
        gooseapp_dir.mkdir()
        config = GooseConfig()
        config.base_path = tmp_path
        errors = config.validate()
        assert len(errors) == 2
        assert any("app.py" in e for e in errors)
        assert any("tests" in e for e in errors)

    def test_validate_success(self, tmp_path: Path) -> None:
        """validate() returns no errors for valid structure."""
        gooseapp_dir = tmp_path / "gooseapp"
        gooseapp_dir.mkdir()
        (gooseapp_dir / "app.py").write_text("")
        (gooseapp_dir / "tests").mkdir()
        config = GooseConfig()
        config.base_path = tmp_path
        errors = config.validate()
        assert errors == []


class TestGooseAppConfig:
    """Tests for goose_app configuration."""

    def test_goose_app_default_none(self) -> None:
        """goose_app is None by default."""
        config = GooseConfig()
        assert config.goose_app is None

    def test_set_and_get_goose_app(self) -> None:
        """Can set and get goose_app."""
        config = GooseConfig()
        app = GooseApp(tools=[], reload_targets=["my_agent"])
        config.goose_app = app

        assert config.goose_app is app
        assert config.goose_app.reload_targets == ["my_agent"]


class TestComputeReloadTargets:
    """Tests for compute_reload_targets method."""

    def test_always_includes_gooseapp(self) -> None:
        """compute_reload_targets always includes gooseapp."""
        config = GooseConfig()
        targets = config.compute_reload_targets()
        assert "gooseapp" in targets

    def test_includes_app_reload_targets(self) -> None:
        """compute_reload_targets includes targets from GooseApp."""
        config = GooseConfig()
        config.goose_app = GooseApp(tools=[], reload_targets=["my_agent", "my_tools"])
        targets = config.compute_reload_targets()
        assert "gooseapp" in targets
        assert "my_agent" in targets
        assert "my_tools" in targets
