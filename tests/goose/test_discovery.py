from __future__ import annotations

import sys
from pathlib import Path

import pytest

from goose.api.config import set_tests_root
from goose.api.schema import TestSummary
from goose.testing.discovery import load_from_qualified_name
from goose.testing.exceptions import UnknownTestError
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


def _clear_suite_paths(monkeypatch, suite_root: Path) -> None:
    removal = {str(suite_root), str(suite_root.parent)}
    new_path = [entry for entry in sys.path if entry not in removal]
    monkeypatch.setattr(sys, "path", new_path, raising=False)


def test_load_from_root_collects_all_modules(tmp_path, monkeypatch):
    sample_root = _write_sample_tests(tmp_path)
    _clear_suite_paths(monkeypatch, sample_root)

    set_tests_root(sample_root)
    definitions = load_from_qualified_name(sample_root.name)

    qualified = sorted(definition.qualified_name for definition in definitions)
    assert qualified == [
        "sample_suite.test_alpha.test_one",
        "sample_suite.test_alpha.test_two",
        "sample_suite.test_beta.test_three",
    ]


def test_load_from_qualified_name_supports_function_and_module(tmp_path, monkeypatch):
    sample_root = _write_sample_tests(tmp_path)
    _clear_suite_paths(monkeypatch, sample_root)

    set_tests_root(sample_root)

    single = load_from_qualified_name("sample_suite.test_alpha.test_one")
    assert [definition.qualified_name for definition in single] == [
        "sample_suite.test_alpha.test_one",
    ]

    module_tests = load_from_qualified_name("sample_suite.test_alpha")
    assert [definition.qualified_name for definition in module_tests] == [
        "sample_suite.test_alpha.test_one",
        "sample_suite.test_alpha.test_two",
    ]


def test_load_from_qualified_name_errors_for_unknown_function(tmp_path, monkeypatch):
    sample_root = _write_sample_tests(tmp_path)
    _clear_suite_paths(monkeypatch, sample_root)

    set_tests_root(sample_root)

    with pytest.raises(UnknownTestError):
        load_from_qualified_name("sample_suite.test_alpha.missing")


def test_load_from_qualified_name_picks_up_file_changes(tmp_path, monkeypatch):
    """Verify that changes to test files are picked up on subsequent loads."""
    sample_root = _write_sample_tests(tmp_path)
    _clear_suite_paths(monkeypatch, sample_root)
    set_tests_root(sample_root)

    definitions = load_from_qualified_name("sample_suite.test_alpha.test_one")
    assert len(definitions) == 1
    original_func = definitions[0].func
    assert original_func() is True

    (sample_root / "test_alpha.py").write_text(
        """
def test_one():
    return "modified"


def test_two():
    return True
""".strip()
        + "\n",
        encoding="utf-8",
    )

    definitions = load_from_qualified_name("sample_suite.test_alpha.test_one")
    assert len(definitions) == 1
    refreshed_func = definitions[0].func
    assert refreshed_func() == "modified"


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
