from __future__ import annotations

import sys
from pathlib import Path

import pytest

from goose.api.config import set_reload_targets, set_tests_root
from goose.api.schema import TestSummary
from goose.testing.discovery import (
    _build_dependency_graph,
    _collect_submodules,
    _is_test_module,
    _topological_sort,
    load_from_qualified_name,
)
from goose.testing.exceptions import TestLoadError, UnknownTestError
from goose.testing.models.tests import TestDefinition


def _write_sample_tests(tmp_path: Path) -> Path:
    root = tmp_path / "sample_suite"
    root.mkdir()
    (root / "__init__.py").write_text("", encoding="utf-8")
    (root / "conftest.py").write_text(
        "from goose.testing import Goose, fixture\n\n@fixture(name='goose')\ndef goose_fixture():\n    return Goose(agent_query_func=lambda q: None)\n",
        encoding="utf-8",
    )
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


# -----------------------------------------------------------------------------
# _is_test_module
# -----------------------------------------------------------------------------


@pytest.mark.parametrize(
    "name,expected",
    [
        ("test_foo", True),
        ("tests_bar", True),
        ("test_", True),
        ("tests_", True),
        ("pkg.test_foo", True),
        ("pkg.subpkg.tests_bar", True),
        ("foo_test", False),
        ("conftest", False),
        ("helper", False),
        ("pkg.conftest", False),
    ],
)
def test_is_test_module(name: str, expected: bool):
    assert _is_test_module(name) == expected


# -----------------------------------------------------------------------------
# _collect_submodules
# -----------------------------------------------------------------------------


def test_collect_submodules_finds_loaded_modules(monkeypatch):
    """Verify _collect_submodules returns modules matching the package prefix."""
    fake_modules = {
        "mypackage": object(),
        "mypackage.sub": object(),
        "mypackage.sub.deep": object(),
        "mypackage.conftest": object(),
        "other": object(),
        "other.sub": object(),
    }
    monkeypatch.setattr(sys, "modules", fake_modules)

    result = _collect_submodules("mypackage")
    assert set(result) == {"mypackage", "mypackage.sub", "mypackage.sub.deep", "mypackage.conftest"}


def test_collect_submodules_excludes_suffix(monkeypatch):
    """Verify exclude_suffix filters out matching modules."""
    fake_modules = {
        "pkg": object(),
        "pkg.test_foo": object(),
        "pkg.conftest": object(),
    }
    monkeypatch.setattr(sys, "modules", fake_modules)

    result = _collect_submodules("pkg", exclude_suffix=".conftest")
    assert set(result) == {"pkg", "pkg.test_foo"}


# -----------------------------------------------------------------------------
# _build_dependency_graph
# -----------------------------------------------------------------------------


def test_build_dependency_graph_detects_imports(monkeypatch):
    """Verify dependency graph correctly identifies cross-module imports."""

    class FakeToolsModule:
        __name__ = "myapp.tools"

    class FakeAgentModule:
        __name__ = "myapp.agent"

    # Agent imports a function from tools
    def tool_func():
        pass

    tool_func.__module__ = "myapp.tools"
    FakeAgentModule.tool_func = tool_func

    fake_modules = {
        "myapp.tools": FakeToolsModule(),
        "myapp.agent": FakeAgentModule(),
    }
    monkeypatch.setattr(sys, "modules", fake_modules)

    modules = {"myapp.tools", "myapp.agent"}
    deps = _build_dependency_graph(modules)

    assert deps["myapp.tools"] == set()
    assert deps["myapp.agent"] == {"myapp.tools"}


def test_build_dependency_graph_handles_missing_modules(monkeypatch):
    """Verify missing modules get empty dependency sets."""
    monkeypatch.setattr(sys, "modules", {})

    modules = {"missing.module"}
    deps = _build_dependency_graph(modules)

    assert deps["missing.module"] == set()


# -----------------------------------------------------------------------------
# _topological_sort
# -----------------------------------------------------------------------------


def test_topological_sort_orders_dependencies_first():
    """Verify dependencies are sorted before dependents."""
    modules = {"a", "b", "c"}
    deps = {
        "a": set(),  # no dependencies
        "b": {"a"},  # b depends on a
        "c": {"b"},  # c depends on b
    }

    result = _topological_sort(modules, deps)

    assert result.index("a") < result.index("b")
    assert result.index("b") < result.index("c")


def test_topological_sort_handles_circular_dependencies():
    """Verify circular dependencies don't cause infinite loop."""
    modules = {"a", "b"}
    deps = {
        "a": {"b"},
        "b": {"a"},
    }

    result = _topological_sort(modules, deps)

    assert set(result) == modules


def test_topological_sort_handles_independent_modules():
    """Verify modules with no dependencies are all included."""
    modules = {"x", "y", "z"}
    deps = {
        "x": set(),
        "y": set(),
        "z": set(),
    }

    result = _topological_sort(modules, deps)

    assert set(result) == modules


# -----------------------------------------------------------------------------
# load_from_qualified_name
# -----------------------------------------------------------------------------


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


def test_load_from_qualified_name_reloads_source_targets(tmp_path, monkeypatch):
    """Verify that reload targets are reloaded before discovering tests."""
    sample_root = _write_sample_tests(tmp_path)
    _clear_suite_paths(monkeypatch, sample_root)
    set_tests_root(sample_root)

    # Create a source package that will be reloaded
    source_pkg = tmp_path / "my_source"
    source_pkg.mkdir()
    (source_pkg / "__init__.py").write_text("", encoding="utf-8")
    (source_pkg / "tools.py").write_text("VALUE = 1\n", encoding="utf-8")

    # Make the source package importable
    sys.path.insert(0, str(tmp_path))
    try:
        import my_source.tools  # noqa: F401

        set_reload_targets(["my_source"])

        # Modify the source file
        (source_pkg / "tools.py").write_text("VALUE = 42\n", encoding="utf-8")

        # Load tests (which triggers source reload)
        load_from_qualified_name("sample_suite")

        # Verify the source module was reloaded
        import my_source.tools as tools_module

        assert tools_module.VALUE == 42
    finally:
        set_reload_targets([])
        sys.path.remove(str(tmp_path))
        # Clean up imported modules
        for name in list(sys.modules):
            if name.startswith("my_source"):
                del sys.modules[name]


# -----------------------------------------------------------------------------
# TestSummary
# -----------------------------------------------------------------------------


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


def test_test_summary_handles_no_docstring():
    def sample_case():
        pass

    definition = TestDefinition(module="pkg.tests", name="test_no_doc", func=sample_case)

    summary = TestSummary.from_definition(definition)

    assert summary.docstring is None


# -----------------------------------------------------------------------------
# Import error propagation
# -----------------------------------------------------------------------------


def test_load_from_qualified_name_propagates_syntax_errors(tmp_path, monkeypatch):
    """Syntax errors in test files should propagate, not be silently swallowed."""
    root = tmp_path / "broken_suite"
    root.mkdir()
    (root / "__init__.py").write_text("", encoding="utf-8")
    (root / "conftest.py").write_text(
        "from goose.testing import Goose, fixture\n\n@fixture(name='goose')\ndef goose_fixture():\n    return Goose(agent_query_func=lambda q: None)\n",
        encoding="utf-8",
    )
    (root / "test_broken.py").write_text(
        """
def test_one():
    return True

this is not valid python syntax!!!
""".strip()
        + "\n",
        encoding="utf-8",
    )

    _clear_suite_paths(monkeypatch, root)
    set_tests_root(root)

    with pytest.raises(TestLoadError) as exc_info:
        load_from_qualified_name("broken_suite")
    assert isinstance(exc_info.value.__cause__, SyntaxError)


def test_load_from_qualified_name_propagates_import_errors(tmp_path, monkeypatch):
    """Import errors (e.g., missing dependencies) should propagate."""
    root = tmp_path / "import_error_suite"
    root.mkdir()
    (root / "__init__.py").write_text("", encoding="utf-8")
    (root / "conftest.py").write_text(
        "from goose.testing import Goose, fixture\n\n@fixture(name='goose')\ndef goose_fixture():\n    return Goose(agent_query_func=lambda q: None)\n",
        encoding="utf-8",
    )
    (root / "test_missing_dep.py").write_text(
        """
from nonexistent_package_xyz import something

def test_one():
    return True
""".strip()
        + "\n",
        encoding="utf-8",
    )

    _clear_suite_paths(monkeypatch, root)
    set_tests_root(root)

    with pytest.raises(TestLoadError) as exc_info:
        load_from_qualified_name("import_error_suite")
    assert isinstance(exc_info.value.__cause__, ModuleNotFoundError)
    assert "nonexistent_package_xyz" in str(exc_info.value.__cause__)


def test_load_from_qualified_name_handles_deleted_file(tmp_path, monkeypatch):
    """Deleting a test file and reloading should not cause persistent errors."""
    root = tmp_path / "delete_suite"
    root.mkdir()
    (root / "__init__.py").write_text("", encoding="utf-8")
    (root / "conftest.py").write_text(
        "from goose.testing import Goose, fixture\n\n"
        "@fixture(name='goose')\n"
        "def goose_fixture():\n"
        "    return Goose(agent_query_func=lambda q: None)\n",
        encoding="utf-8",
    )
    test_file = root / "test_deletable.py"
    test_file.write_text(
        "def test_will_be_deleted():\n    return True\n",
        encoding="utf-8",
    )

    _clear_suite_paths(monkeypatch, root)
    set_tests_root(root)

    # First load succeeds
    definitions = load_from_qualified_name("delete_suite")
    assert len(definitions) == 1
    assert definitions[0].name == "test_will_be_deleted"

    # Delete the test file
    test_file.unlink()

    # Second load should succeed with empty list (no tests found)
    definitions = load_from_qualified_name("delete_suite")
    assert definitions == []
