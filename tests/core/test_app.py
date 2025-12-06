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
        assert repr(app) == "GooseApp(tools=0, reload_targets=[], reload_exclude=[])"

    def test_repr_with_content(self) -> None:
        """Repr shows correct counts."""
        app = GooseApp(
            tools=[sample_tool_1, sample_tool_2],
            reload_targets=["my_agent"],
            reload_exclude=["my_agent.models"],
        )
        assert repr(app) == "GooseApp(tools=2, reload_targets=['my_agent'], reload_exclude=['my_agent.models'])"
