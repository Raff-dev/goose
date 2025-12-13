"""GooseApp - central configuration for Goose dashboard."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any


class GooseApp:
    """Central configuration for Goose dashboard.

    This is the main entry point for configuring Goose. Users create a GooseApp
    instance in their gooseapp/app.py file, passing tools, agents, and reload targets.

    Example:
        from goose import GooseApp
        from my_agent.tools import get_products, create_order
        from my_agent.agent import get_agent

        app = GooseApp(
            tools=[get_products, create_order],
            agents=[
                {
                    "name": "My Agent",
                    "get_agent": get_agent,
                    "models": ["gpt-4o-mini", "gpt-4o"],
                },
            ],
            reload_targets=["my_agent"],
            reload_exclude=["my_agent.models"],  # Skip reloading models
        )
    """

    def __init__(
        self,
        tools: Sequence[Callable[..., Any]] | None = None,
        agents: list[dict[str, Any]] | None = None,
        reload_targets: list[str] | None = None,
        reload_exclude: list[str] | None = None,
    ) -> None:
        """Initialize GooseApp.

        Args:
            tools: List of LangChain @tool decorated functions to expose in the
                   tooling dashboard.
            agents: List of agent config dicts for the chatting dashboard.
                   Each dict must have: name (str), get_agent (callable), models (list[str]).
            reload_targets: List of module names to reload when files change.
                           The gooseapp module is always included automatically.
            reload_exclude: List of module name prefixes to exclude from reloading.
                           Useful for modules like Django models that shouldn't be reloaded.
        """
        self.tools: list[Callable[..., Any]] = list(tools) if tools is not None else []
        self.reload_targets: list[str] = reload_targets if reload_targets is not None else []
        self.reload_exclude: list[str] = reload_exclude if reload_exclude is not None else []

        # Process agents - assign sequential IDs and build lookup dict
        self._agents_by_id: dict[str, dict[str, Any]] = {}
        for idx, agent_config in enumerate(agents or [], start=1):
            self._validate_agent_config(agent_config)
            agent_id = str(idx)
            self._agents_by_id[agent_id] = {
                "id": agent_id,
                **agent_config,
            }

        # Validate unique names
        names = [a["name"] for a in self._agents_by_id.values()]
        if len(names) != len(set(names)):
            raise ValueError("Agent names must be unique")

    def _validate_agent_config(self, config: dict[str, Any]) -> None:
        """Validate an agent config dict has required fields."""
        required = {"name", "get_agent", "models"}
        missing = required - set(config.keys())
        if missing:
            raise ValueError(f"Agent config missing required fields: {missing}")
        if not callable(config["get_agent"]):
            raise ValueError("Agent 'get_agent' must be callable")
        if not isinstance(config["models"], list) or not config["models"]:
            raise ValueError("Agent 'models' must be a non-empty list")

    @property
    def agents(self) -> list[dict[str, Any]]:
        """Return list of agent configs with IDs."""
        return list(self._agents_by_id.values())

    def get_agent_config(self, agent_id: str) -> dict[str, Any] | None:
        """Get agent config by ID."""
        return self._agents_by_id.get(agent_id)

    def __repr__(self) -> str:
        return (
            f"GooseApp(tools={len(self.tools)}, "
            f"agents={len(self._agents_by_id)}, "
            f"reload_targets={self.reload_targets}, "
            f"reload_exclude={self.reload_exclude})"
        )
