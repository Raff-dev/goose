from __future__ import annotations

from pathlib import Path

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
