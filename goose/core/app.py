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
        from langchain_openai import ChatOpenAI
        from langgraph.prebuilt import create_react_agent
        from my_agent.tools import get_products, create_order

        agent = create_react_agent(
            ChatOpenAI(model="gpt-4o-mini"),
            tools=[get_products, create_order],
        )
        agent.name = "My Agent"

        # Option 1: Simple flat list of tools
        app = GooseApp(
            tools=[get_products, create_order],
            agents=[agent],
        )

        # Option 2: Grouped tools for UI organization
        app = GooseApp(
            tool_groups={
                "Products": [get_products],
                "Orders": [create_order],
            },
            agents=[agent],
        )
    """

    def __init__(
        self,
        tools: Sequence[Callable[..., Any]] | None = None,
        tool_groups: dict[str, Sequence[Callable[..., Any]]] | None = None,
        *,
        agents: Sequence[Any] | None = None,
        reload_targets: list[str] | None = None,
        reload_exclude: list[str] | None = None,
    ) -> None:
        """Initialize GooseApp.

        Args:
            tools: List of LangChain @tool decorated functions. Cannot be used with tool_groups.
            tool_groups: Dict mapping group names to lists of tools. Cannot be used with tools.
            agents: List of pre-built LangChain agents. Each agent must have a `name`
                   attribute set (e.g., `agent.name = "My Agent"`).
            reload_targets: List of module names to reload when files change.
                           The gooseapp module is always included automatically.
            reload_exclude: List of module name prefixes to exclude from reloading.
                           Useful for modules like Django models that shouldn't be reloaded.

        Raises:
            ValueError: If both tools and tool_groups are provided.
        """
        if tools is not None and tool_groups is not None:
            raise ValueError("Cannot specify both 'tools' and 'tool_groups'. Use one or the other.")

        self.reload_targets: list[str] = reload_targets if reload_targets is not None else []
        self.reload_exclude: list[str] = reload_exclude if reload_exclude is not None else []

        # Build tool name -> group mapping and collect all tools
        self._tool_groups: dict[str, str] = {}
        tools_list: list[Callable[..., Any]] = []

        if tool_groups:
            for group_name, group_tools in tool_groups.items():
                for tool in group_tools:
                    tool_name = getattr(tool, "name", None) or getattr(tool, "__name__", None)
                    if tool_name:
                        self._tool_groups[tool_name] = group_name
                    tools_list.append(tool)
        elif tools:
            tools_list = list(tools)

        self.tools: list[Callable[..., Any]] = tools_list

        # Process agents - assign sequential IDs and build lookup dict
        self._agents_by_id: dict[str, dict[str, Any]] = {}
        for idx, agent in enumerate(agents or [], start=1):
            self._validate_agent(agent)
            agent_id = str(idx)
            self._agents_by_id[agent_id] = {
                "id": agent_id,
                "name": agent.name,
                "agent": agent,
            }

        # Validate unique names
        names = [a["name"] for a in self._agents_by_id.values()]
        if len(names) != len(set(names)):
            raise ValueError("Agent names must be unique")

    def _validate_agent(self, agent: Any) -> None:
        """Validate an agent has required attributes."""
        if not hasattr(agent, "name") or not agent.name:
            raise ValueError("Agent must have a 'name' attribute set (e.g., agent.name = 'My Agent')")

    def get_tool_group(self, tool_name: str) -> str | None:
        """Get the group name for a tool."""
        return self._tool_groups.get(tool_name)

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
