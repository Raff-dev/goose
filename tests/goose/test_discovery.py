from __future__ import annotations

import sys
from pathlib import Path
from types import ModuleType

from goose.api.schema import TestSummary
from goose.testing.discovery import discover_tests, load_from_qualified_name
from goose.testing.models.tests import TestDefinition


def _write_sample_tests(tmp_path: Path) -> Path:
    root = tmp_path / "sample_suite"
    root.mkdir()
    (root / "__init__.py").write_text("", encoding="utf-8")
    (root / "test_alpha.py").write_text(
        """
def test_one():
    return True


def test_two():
    return True
""".strip()
        + "\n",
        encoding="utf-8",
    )
    (root / "test_beta.py").write_text(
        """
def test_three():
    return True
""".strip()
        + "\n",
        encoding="utf-8",
    )
    return root


def _write_reloadable_suite(tmp_path: Path, package_name: str) -> tuple[Path, Path]:
    root = tmp_path / package_name
    root.mkdir()
    (root / "__init__.py").write_text("", encoding="utf-8")
    helper_path = root / "helpers.py"
    helper_path.write_text(
        """
def current_value():
    return "first"
""".strip()
        + "\n",
        encoding="utf-8",
    )
    (root / "test_reload.py").write_text(
        """
from {package}.helpers import current_value


def test_marker():
    return current_value()
""".strip().format(
            package=package_name
        )
        + "\n",
        encoding="utf-8",
    )
    return root, helper_path


def _write_fixture_suite(tmp_path: Path) -> Path:
    root = tmp_path / "fixture_suite"
    root.mkdir()
    (root / "__init__.py").write_text("", encoding="utf-8")
    (root / "conftest.py").write_text(
        """
from goose.testing import fixture


@fixture()
def setup_data():
    return "data"
""".strip()
        + "\n",
        encoding="utf-8",
    )
    (root / "test_sample.py").write_text(
        """
def test_dummy():
    return True
""".strip()
        + "\n",
        encoding="utf-8",
    )
    return root


def test_discover_tests_collects_all_modules(tmp_path, monkeypatch):
    sample_root = _write_sample_tests(tmp_path)
    monkeypatch.syspath_prepend(str(tmp_path))

    definitions = discover_tests(sample_root)

    qualified = sorted(definition.qualified_name for definition in definitions)
    assert qualified == [
        "sample_suite.test_alpha.test_one",
        "sample_suite.test_alpha.test_two",
        "sample_suite.test_beta.test_three",
    ]


def test_load_from_qualified_name_supports_function_and_module(tmp_path, monkeypatch):
    _write_sample_tests(tmp_path)
    monkeypatch.syspath_prepend(str(tmp_path))

    single = load_from_qualified_name("sample_suite.test_alpha.test_one")
    assert [definition.qualified_name for definition in single] == [
        "sample_suite.test_alpha.test_one",
    ]

    module_defs = load_from_qualified_name("sample_suite.test_alpha")
    assert sorted(definition.qualified_name for definition in module_defs) == [
        "sample_suite.test_alpha.test_one",
        "sample_suite.test_alpha.test_two",
    ]


def test_discover_tests_reloads_project_modules(tmp_path, monkeypatch):
    suite_root, helper_path = _write_reloadable_suite(tmp_path, "reload_suite_discover")
    monkeypatch.syspath_prepend(str(tmp_path))

    first = discover_tests(suite_root)
    assert len(first) == 1
    assert first[0].func() == "first"

    helper_path.write_text(
        """
def current_value():
    return "second"
""".strip()
        + "\n",
        encoding="utf-8",
    )

    second = discover_tests(suite_root)
    assert len(second) == 1
    assert second[0].func() == "second"


def test_load_from_qualified_name_reloads_project_modules(tmp_path, monkeypatch):
    suite_root, helper_path = _write_reloadable_suite(tmp_path, "reload_suite_load")
    monkeypatch.syspath_prepend(str(tmp_path))

    first = load_from_qualified_name("reload_suite_load.test_reload.test_marker", tests_root=suite_root)
    assert len(first) == 1
    assert first[0].func() == "first"

    helper_path.write_text(
        """
def current_value():
    return "updated"
""".strip()
        + "\n",
        encoding="utf-8",
    )

    second = load_from_qualified_name("reload_suite_load.test_reload.test_marker", tests_root=suite_root)
    assert len(second) == 1
    assert second[0].func() == "updated"


def test_discover_tests_resets_fixture_registry(tmp_path, monkeypatch):
    suite_root = _write_fixture_suite(tmp_path)
    monkeypatch.syspath_prepend(str(tmp_path))

    first = discover_tests(suite_root)
    assert len(first) == 1

    second = discover_tests(suite_root)
    assert len(second) == 1


def test_purge_project_modules_skips_virtualenv(tmp_path):
    from goose.testing import discovery as discovery_module

    project_root = tmp_path
    virtual_module_path = project_root / ".venv" / "lib" / "python3.13" / "site-packages" / "pkg" / "mod.py"
    virtual_module_path.parent.mkdir(parents=True)
    virtual_module_path.write_text("value = 1\n", encoding="utf-8")

    fake_module = ModuleType("fake_pkg")
    fake_module.__file__ = str(virtual_module_path)

    sys.modules["fake_pkg"] = fake_module
    try:
        discovery_module._purge_project_modules(project_root)
        assert "fake_pkg" in sys.modules
    finally:
        sys.modules.pop("fake_pkg", None)


def test_test_summary_serializes_definition_docstring():
    def sample_case():
        """Only the first line is kept.

        Additional description should be ignored.
        """

    definition = TestDefinition(module="pkg.tests", name="test_example", func=sample_case)

    summary = TestSummary.from_definition(definition)

    assert summary.qualified_name == "pkg.tests.test_example"
    assert summary.module == "pkg.tests"
    assert summary.name == "test_example"
    assert summary.docstring == "Only the first line is kept."
