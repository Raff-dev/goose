"""Fixture system for Goose tests."""

from __future__ import annotations

import inspect
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from goose.testing.engine import Goose


@dataclass
class FixtureDefinition:
    """Single registered fixture."""

    func: Callable[..., Any]
    autouse: bool = False


fixtures: dict[str, FixtureDefinition] = {}


def register(name: str, func: Callable[..., Any], *, autouse: bool = False) -> None:
    """Register a fixture factory under *name*.

    Args:
        name: The name to register the fixture under.
        func: The fixture factory function.
        autouse: Whether to apply this fixture automatically to all tests.
    """

    if name in fixtures:
        raise ValueError(f"Fixture '{name}' already registered")
    fixtures[name] = FixtureDefinition(func=func, autouse=autouse)


def reset_registry() -> None:
    """Clear all registered fixtures.

    Useful when test modules are reloaded to avoid duplicate registration errors.
    """

    fixtures.clear()


def _resolve(name: str, cache: dict[str, Any]) -> Any:
    """Resolve a fixture by name: run its factory function with resolved dependencies, cache the result.

    This handles dependency injection for fixtures, ensuring each fixture is computed once,
    detecting circular dependencies, and storing results in the cache for reuse.

    Args:
        name: The name of the fixture to resolve.
        cache: Mutable dict to cache resolved fixture values and track resolution state.

    Returns:
        The computed value of the fixture.
    """

    definition = fixtures.get(name)
    if definition is None:
        raise KeyError(f"Unknown fixture '{name}'")

    cached = cache.get(name, _MISSING)
    if cached is _RESOLVING:
        raise RuntimeError(f"Circular fixture dependency detected for '{name}'")
    if cached is not _MISSING:
        return cached

    cache[name] = _RESOLVING
    try:
        parameters = inspect.signature(definition.func).parameters
        kwargs = {param: _resolve(param, cache) for param in parameters}
        value = definition.func(**kwargs)
    except Exception:  # pragma: no cover - propagate after cleanup
        cache.pop(name, None)
        raise
    cache[name] = value
    return value


def apply_autouse(cache: dict[str, Any]) -> None:
    """Populate autouse fixtures into *cache*.

    Args:
        cache: The cache dict to populate with autouse fixture values.
    """

    for name, definition in fixtures.items():
        if definition.autouse:
            _resolve(name, cache)


_MISSING = object()
_RESOLVING = object()


def fixture(*, name: str | None = None, autouse: bool = False):
    """Decorator to register fixtures with the Goose registry.

    Args:
        name: Optional custom name for the fixture. Defaults to the function name.
        autouse: Whether to apply this fixture automatically to all tests.

    Returns:
        The decorator function.
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        fixture_name = name or func.__name__
        register(fixture_name, func, autouse=autouse)
        return func

    return decorator


def build_call_arguments(func: Callable[..., Any], cache: dict[str, Any]) -> dict[str, Any]:
    """Resolve fixtures required by *func* using *cache*.

    Args:
        func: The function whose parameters need fixture resolution.
        cache: The cache dict containing resolved fixture values.

    Returns:
        A dict of parameter names to resolved fixture values.
    """

    parameters = inspect.signature(func).parameters
    return {param: _resolve(param, cache) for param in parameters}


def extract_goose_fixture(cache: dict[str, Any]) -> Goose:
    """Extract the Goose fixture instance from the cache.

    Args:
        cache: The fixture cache containing resolved values.

    Returns:
        The Goose instance.

    Raises:
        AssertionError: If no Goose fixture is found in the cache.
    """
    for value in cache.values():
        if isinstance(value, Goose):
            return value

    raise AssertionError("No Goose fixture available to retrieve execution history.")


__all__ = [
    "fixture",
    "build_call_arguments",
    "extract_goose_fixture",
    "reset_registry",
]
