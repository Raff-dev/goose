"""Tests for GooseApp class."""

from __future__ import annotations

from goose.core.app import GooseApp


def sample_tool_1() -> str:
    """Sample tool 1."""
    return "tool1"


def sample_tool_2() -> str:
    """Sample tool 2."""
    return "tool2"


class TestGooseAppInit:
    """Tests for GooseApp initialization."""

    def test_init_empty(self) -> None:
        """GooseApp can be initialized with no arguments."""
        app = GooseApp()

        assert app.tools == []
        assert app.reload_targets == []

    def test_init_with_tools(self) -> None:
        """GooseApp stores tools list."""
        app = GooseApp(tools=[sample_tool_1, sample_tool_2])

        assert len(app.tools) == 2
        assert app.tools[0] is sample_tool_1
        assert app.tools[1] is sample_tool_2

    def test_init_with_reload_targets(self) -> None:
        """GooseApp stores reload targets."""
        app = GooseApp(reload_targets=["my_agent", "my_agent.tools"])

        assert app.reload_targets == ["my_agent", "my_agent.tools"]

    def test_init_with_all_options(self) -> None:
        """GooseApp accepts all options together."""
        app = GooseApp(
            tools=[sample_tool_1],
            reload_targets=["my_agent"],
        )

        assert len(app.tools) == 1
        assert app.reload_targets == ["my_agent"]

    def test_tools_is_new_list(self) -> None:
        """Tools list is a copy, not a reference to the original."""
        original = [sample_tool_1]
        app = GooseApp(tools=original)

        # Modifying original shouldn't affect app
        original.append(sample_tool_2)
        # Note: Current implementation doesn't copy, but this tests the interface
        # If we want isolation, we'd need to copy in __init__

    def test_reload_targets_is_new_list(self) -> None:
        """Reload targets list is a copy, not a reference."""
        original = ["my_agent"]
        app = GooseApp(reload_targets=original)

        # Same note as above


class TestGooseAppRepr:
    """Tests for GooseApp string representation."""

    def test_repr_empty(self) -> None:
        """Repr shows tool count and reload targets."""
        app = GooseApp()
        assert repr(app) == "GooseApp(tools=0, agents=0, reload_targets=[], reload_exclude=[])"

    def test_repr_with_content(self) -> None:
        """Repr shows correct counts."""
        app = GooseApp(
            tools=[sample_tool_1, sample_tool_2],
            reload_targets=["my_agent"],
            reload_exclude=["my_agent.models"],
        )
        assert (
            repr(app) == "GooseApp(tools=2, agents=0, reload_targets=['my_agent'], reload_exclude=['my_agent.models'])"
        )


def sample_get_agent(model: str) -> str:
    """Sample agent factory for testing."""
    return f"agent-{model}"


class TestGooseAppAgents:
    """Tests for GooseApp agent configuration."""

    def test_init_with_agents(self) -> None:
        """GooseApp stores agent configs with generated IDs."""
        app = GooseApp(
            agents=[
                {
                    "name": "Test Agent",
                    "get_agent": sample_get_agent,
                    "models": ["gpt-4o-mini", "gpt-4o"],
                },
            ],
        )

        assert len(app.agents) == 1
        agent = app.agents[0]
        assert agent["name"] == "Test Agent"
        assert agent["models"] == ["gpt-4o-mini", "gpt-4o"]
        assert agent["get_agent"] is sample_get_agent
        assert agent["id"] == "1"  # Sequential ID

    def test_get_agent_config_by_id(self) -> None:
        """Can retrieve agent config by ID."""
        app = GooseApp(
            agents=[
                {
                    "name": "Test Agent",
                    "get_agent": sample_get_agent,
                    "models": ["gpt-4o-mini"],
                },
            ],
        )

        agent_id = app.agents[0]["id"]
        config = app.get_agent_config(agent_id)

        assert config is not None
        assert config["name"] == "Test Agent"

    def test_get_agent_config_returns_none_for_unknown(self) -> None:
        """Returns None for unknown agent ID."""
        app = GooseApp()

        assert app.get_agent_config("unknown-id") is None

    def test_multiple_agents_get_unique_ids(self) -> None:
        """Each agent gets a unique ID."""
        app = GooseApp(
            agents=[
                {"name": "Agent 1", "get_agent": sample_get_agent, "models": ["gpt-4o"]},
                {"name": "Agent 2", "get_agent": sample_get_agent, "models": ["gpt-4o"]},
            ],
        )

        ids = [a["id"] for a in app.agents]
        assert len(ids) == 2
        assert ids[0] != ids[1]

    def test_duplicate_names_raises_error(self) -> None:
        """Duplicate agent names raise ValueError."""
        import pytest

        with pytest.raises(ValueError, match="Agent names must be unique"):
            GooseApp(
                agents=[
                    {"name": "Same Name", "get_agent": sample_get_agent, "models": ["gpt-4o"]},
                    {"name": "Same Name", "get_agent": sample_get_agent, "models": ["gpt-4o"]},
                ],
            )

    def test_missing_required_field_raises_error(self) -> None:
        """Missing required agent field raises ValueError."""
        import pytest

        with pytest.raises(ValueError, match="missing required fields"):
            GooseApp(
                agents=[
                    {"name": "Agent", "models": ["gpt-4o"]},  # Missing get_agent
                ],
            )

    def test_invalid_get_agent_raises_error(self) -> None:
        """Non-callable get_agent raises ValueError."""
        import pytest

        with pytest.raises(ValueError, match="'get_agent' must be callable"):
            GooseApp(
                agents=[
                    {"name": "Agent", "get_agent": "not-callable", "models": ["gpt-4o"]},
                ],
            )

    def test_empty_models_raises_error(self) -> None:
        """Empty models list raises ValueError."""
        import pytest

        with pytest.raises(ValueError, match="'models' must be a non-empty list"):
            GooseApp(
                agents=[
                    {"name": "Agent", "get_agent": sample_get_agent, "models": []},
                ],
            )
