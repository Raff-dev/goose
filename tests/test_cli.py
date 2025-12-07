"""Tests for the Goose CLI structure."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from typer.testing import CliRunner

from goose.cli import app

runner = CliRunner()


class TestCLIStructure:
    """Tests for CLI command structure."""

    def test_main_app_exists(self) -> None:
        """Main app is accessible."""
        assert app is not None

    def test_help_shows_commands(self) -> None:
        """Help output shows available commands."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "init" in result.output
        assert "api" in result.output
        assert "test" in result.output

    def test_test_subcommand_has_run_and_list(self) -> None:
        """Test subcommand has run and list commands."""
        result = runner.invoke(app, ["test", "--help"])
        assert result.exit_code == 0
        assert "run" in result.output
        assert "list" in result.output


class TestGooseInit:
    """Tests for goose init command."""

    def test_init_creates_gooseapp_structure(self, tmp_path: Path) -> None:
        """goose init creates the expected folder structure."""
        result = runner.invoke(app, ["init", str(tmp_path)])

        assert result.exit_code == 0
        assert (tmp_path / "gooseapp").exists()
        assert (tmp_path / "gooseapp" / "__init__.py").exists()
        assert (tmp_path / "gooseapp" / "app.py").exists()
        assert (tmp_path / "gooseapp" / "conftest.py").exists()  # At package root for discovery
        assert (tmp_path / "gooseapp" / "tests").exists()
        assert (tmp_path / "gooseapp" / "tests" / "__init__.py").exists()

    def test_init_app_py_contains_gooseapp(self, tmp_path: Path) -> None:
        """Generated app.py imports GooseApp."""
        runner.invoke(app, ["init", str(tmp_path)])

        app_content = (tmp_path / "gooseapp" / "app.py").read_text()
        assert "from goose import GooseApp" in app_content
        assert "app = GooseApp(" in app_content

    def test_init_conftest_contains_fixture(self, tmp_path: Path) -> None:
        """Generated conftest.py has goose fixture."""
        runner.invoke(app, ["init", str(tmp_path)])

        conftest_content = (tmp_path / "gooseapp" / "conftest.py").read_text()
        assert "@fixture" in conftest_content
        assert "def goose(" in conftest_content

    def test_init_fails_if_exists_without_force(self, tmp_path: Path) -> None:
        """goose init fails if gooseapp already exists."""
        (tmp_path / "gooseapp").mkdir()

        result = runner.invoke(app, ["init", str(tmp_path)])

        assert result.exit_code == 1
        assert "already exists" in result.output

    def test_init_force_overwrites(self, tmp_path: Path) -> None:
        """goose init --force overwrites existing files."""
        (tmp_path / "gooseapp").mkdir()
        (tmp_path / "gooseapp" / "old_file.txt").write_text("old")

        result = runner.invoke(app, ["init", str(tmp_path), "--force"])

        assert result.exit_code == 0
        assert (tmp_path / "gooseapp" / "app.py").exists()


class TestGooseApi:
    """Tests for goose api command."""

    def test_api_requires_gooseapp_directory(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """goose api fails when gooseapp/ directory doesn't exist."""
        monkeypatch.chdir(tmp_path)

        result = runner.invoke(app, ["api"])

        assert result.exit_code != 0
        assert "Invalid gooseapp/ structure" in result.output or "not found" in result.output

    def test_api_validates_gooseapp_structure(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """goose api validates gooseapp/ has required files."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / "gooseapp").mkdir()

        result = runner.invoke(app, ["api"])

        assert result.exit_code != 0
        assert "app.py" in result.output or "tests" in result.output

    def test_api_validates_app_loadable(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """goose api validates that gooseapp/app.py can be imported."""
        # Remove any cached gooseapp module
        modules_to_remove = [k for k in sys.modules if k.startswith("gooseapp")]
        for mod in modules_to_remove:
            del sys.modules[mod]

        monkeypatch.chdir(tmp_path)

        # Create a gooseapp with a syntax error (not ImportError which could be caught)
        gooseapp_dir = tmp_path / "gooseapp"
        gooseapp_dir.mkdir()
        (gooseapp_dir / "__init__.py").write_text("")
        (gooseapp_dir / "app.py").write_text("app = 'not a GooseApp'")  # Wrong type
        (gooseapp_dir / "tests").mkdir()

        # Ensure tmp_path is at the start of sys.path
        monkeypatch.syspath_prepend(str(tmp_path))

        result = runner.invoke(app, ["api"])

        # Cleanup module cache
        modules_to_remove = [k for k in sys.modules if k.startswith("gooseapp")]
        for mod in modules_to_remove:
            del sys.modules[mod]

        assert result.exit_code != 0
        assert "Error loading" in result.output


class TestGooseTestRun:
    """Tests for goose test run command."""

    def test_test_run_with_nonexistent_target(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """goose test run fails for nonexistent target."""
        monkeypatch.chdir(tmp_path)

        result = runner.invoke(app, ["test", "run", "nonexistent_tests"])

        assert result.exit_code != 0


class TestGooseTestList:
    """Tests for goose test list command."""

    def test_test_list_with_nonexistent_target(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """goose test list fails for nonexistent target."""
        monkeypatch.chdir(tmp_path)

        result = runner.invoke(app, ["test", "list", "nonexistent_tests"])

        assert result.exit_code != 0
