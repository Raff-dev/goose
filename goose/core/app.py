"""GooseApp - central configuration for Goose dashboard."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any


class GooseApp:
    """Central configuration for Goose dashboard.

    This is the main entry point for configuring Goose. Users create a GooseApp
    instance in their gooseapp/app.py file, passing tools and reload targets.

    Example:
        from goose import GooseApp
        from my_agent.tools import get_products, create_order

        app = GooseApp(
            tools=[get_products, create_order],
            reload_targets=["my_agent"],
            reload_exclude=["my_agent.models"],  # Skip reloading models
        )
    """

    def __init__(
        self,
        tools: Sequence[Callable[..., Any]] | None = None,
        reload_targets: list[str] | None = None,
        reload_exclude: list[str] | None = None,
    ) -> None:
        """Initialize GooseApp.

        Args:
            tools: List of LangChain @tool decorated functions to expose in the
                   tooling dashboard.
            reload_targets: List of module names to reload when files change.
                           The gooseapp module is always included automatically.
            reload_exclude: List of module name prefixes to exclude from reloading.
                           Useful for modules like Django models that shouldn't be reloaded.
        """
        self.tools: list[Callable[..., Any]] = list(tools) if tools is not None else []
        self.reload_targets: list[str] = reload_targets if reload_targets is not None else []
        self.reload_exclude: list[str] = reload_exclude if reload_exclude is not None else []

    def __repr__(self) -> str:
        return (
            f"GooseApp(tools={len(self.tools)}, "
            f"reload_targets={self.reload_targets}, "
            f"reload_exclude={self.reload_exclude})"
        )
