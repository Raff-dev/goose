"""Fixture system for Goose tests."""

from __future__ import annotations

import asyncio
import inspect
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class FixtureDefinition:
    """Single registered fixture."""

    func: Callable[..., Any]
    autouse: bool = False


class FixtureRegistry:
    """Lightweight fixture container inspired by pytest."""

    def __init__(self) -> None:
        self._fixtures: dict[str, FixtureDefinition] = {}

    def register(self, name: str, func: Callable[..., Any], *, autouse: bool = False) -> None:
        """Register a fixture factory under *name*."""

        if name in self._fixtures:
            raise ValueError(f"Fixture '{name}' already registered")
        self._fixtures[name] = FixtureDefinition(func=func, autouse=autouse)

    def resolve(self, name: str, cache: dict[str, Any]) -> Any:
        """Resolve a fixture value, caching the result in *cache*."""

        definition = self._fixtures.get(name)
        if definition is None:
            raise KeyError(f"Unknown fixture '{name}'")

        cached = cache.get(name, _MISSING)
        if cached is _RESOLVING:
            raise RuntimeError(f"Circular fixture dependency detected for '{name}'")
        if cached is not _MISSING:
            return cached

        cache[name] = _RESOLVING
        try:
            value = self._invoke(definition.func, cache)
        except Exception:  # pragma: no cover - propagate after cleanup
            cache.pop(name, None)
            raise
        cache[name] = value
        return value

    def apply_autouse(self, cache: dict[str, Any]) -> None:
        """Populate autouse fixtures into *cache*."""

        for name, definition in self._fixtures.items():
            if definition.autouse:
                self.resolve(name, cache)

    def _invoke(self, func: Callable[..., Any], cache: dict[str, Any]) -> Any:
        """Invoke *func* with fixture arguments resolved from *cache*."""

        parameters = inspect.signature(func).parameters
        kwargs = {param: self.resolve(param, cache) for param in parameters}

        if inspect.iscoroutinefunction(func):
            return asyncio.run(func(**kwargs))

        result = func(**kwargs)
        if inspect.iscoroutine(result):
            return asyncio.run(result)
        return result


_MISSING = object()
_RESOLVING = object()
FIXTURE_REGISTRY = FixtureRegistry()


def fixture(*, name: str | None = None, autouse: bool = False):
    """Decorator to register fixtures with the Goose registry."""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        fixture_name = name or func.__name__
        FIXTURE_REGISTRY.register(fixture_name, func, autouse=autouse)
        return func

    return decorator


def build_call_arguments(func: Callable[..., Any], cache: dict[str, Any]) -> dict[str, Any]:
    """Resolve fixtures required by *func* using *cache*."""

    parameters = inspect.signature(func).parameters
    return {param: FIXTURE_REGISTRY.resolve(param, cache) for param in parameters}


__all__ = [
    "FixtureRegistry",
    "fixture",
    "FIXTURE_REGISTRY",
    "build_call_arguments",
]
