from __future__ import annotations

import pytest

from goose.testing.engine import Goose
from goose.testing.fixtures import build_call_arguments, extract_goose_fixture, fixture, fixtures, register


@pytest.fixture(autouse=True)
def clear_registry():
    fixtures.clear()
    yield
    fixtures.clear()


def test_register_rejects_duplicates():
    def sample():
        return "value"

    register("sample", sample)
    with pytest.raises(ValueError, match="already registered"):
        register("sample", sample)


def test_fixture_decorator_registers_name():
    @fixture(name="custom")
    def provide():
        return 42

    assert "custom" in fixtures
    assert fixtures["custom"].func is provide


def test_build_call_arguments_resolves_dependencies():
    @fixture()
    def dependency():
        return "dep"

    @fixture()
    def target(dependency: str):
        return f"value-{dependency}"

    cache = {}

    kwargs = build_call_arguments(target, cache)

    assert kwargs == {"dependency": "dep"}
    assert cache["dependency"] == "dep"


def test_fixture_resolution_detects_cycles():
    @fixture()
    def first(second):  # type: ignore[no-redef]
        return second

    @fixture()
    def second(first):  # type: ignore[no-redef]
        return first

    cache = {}
    with pytest.raises(RuntimeError, match="Circular fixture dependency"):
        build_call_arguments(first, cache)


def test_extract_goose_fixture_pulls_instance():
    sentinel = Goose(agent_query_func=lambda query: None, validator_model="gpt-4o-mini")
    cache = {"goose": sentinel}

    extracted = extract_goose_fixture(cache)
    assert extracted is sentinel

    with pytest.raises(AssertionError):
        extract_goose_fixture({})
