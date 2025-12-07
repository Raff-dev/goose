"""Tests for tooling API routes."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient

from goose.app import app
from goose.core.app import GooseApp
from goose.core.config import GooseConfig

client = TestClient(app)


# Mock tool for testing
class MockTool:
    """Mock LangChain tool."""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.args_schema = None

    def invoke(self, args: dict[str, Any]) -> str:
        return f"Result for {self.name}: {args}"

    def __call__(self, **kwargs: Any) -> str:
        return self.invoke(kwargs)


@pytest.fixture(autouse=True)
def reset_config() -> Iterator[None]:
    """Reset GooseConfig singleton before each test."""
    GooseConfig.reset()
    yield
    GooseConfig.reset()


@pytest.fixture
def mock_goose_app() -> GooseApp:
    """Create a GooseApp with mock tools."""
    tools = [
        MockTool("get_weather", "Get weather for a location"),
        MockTool("search", "Search for information"),
    ]
    return GooseApp(tools=tools)


@pytest.fixture
def setup_goose_app(mock_goose_app: GooseApp) -> Iterator[GooseApp]:
    """Set up and tear down GooseApp in config."""
    config = GooseConfig()
    config.goose_app = mock_goose_app
    yield mock_goose_app
    config.goose_app = None


class TestListTools:
    """Tests for GET /tooling/tools."""

    def test_returns_empty_when_no_app(self) -> None:
        """Returns empty list when no GooseApp configured."""
        config = GooseConfig()
        config.goose_app = None

        response = client.get("/tooling/tools")

        assert response.status_code == 200
        assert response.json() == []

    def test_returns_tool_summaries(self, setup_goose_app: GooseApp) -> None:
        """Returns tool summaries with name, description, parameter_count."""
        response = client.get("/tooling/tools")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["name"] == "get_weather"
        assert data[0]["description"] == "Get weather for a location"
        assert "parameter_count" in data[0]


class TestGetTool:
    """Tests for GET /tooling/tools/{name}."""

    def test_returns_tool_detail(self, setup_goose_app) -> None:
        """Returns detailed tool information."""
        response = client.get("/tooling/tools/get_weather")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "get_weather"
        assert data["description"] == "Get weather for a location"
        assert "parameters" in data

    def test_returns_404_for_unknown_tool(self, setup_goose_app) -> None:
        """Returns 404 for unknown tool name."""
        response = client.get("/tooling/tools/nonexistent")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestInvokeTool:
    """Tests for POST /tooling/tools/{name}/invoke."""

    def test_invokes_tool_successfully(self, setup_goose_app) -> None:
        """Successfully invokes a tool and returns result."""
        response = client.post(
            "/tooling/tools/get_weather/invoke",
            json={"args": {"location": "London"}},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Result for get_weather" in data["result"]
        assert data["error"] is None

    def test_returns_404_for_unknown_tool(self, setup_goose_app) -> None:
        """Returns 404 when invoking unknown tool."""
        response = client.post(
            "/tooling/tools/nonexistent/invoke",
            json={"args": {}},
        )

        assert response.status_code == 404

    def test_returns_error_on_failure(self, setup_goose_app: GooseApp) -> None:
        """Returns error when tool execution fails."""
        # Create a tool that raises an error

        class FailingTool:
            name = "failing_tool"
            description = "Always fails"
            args_schema = None

            def invoke(self, args: dict[str, Any]) -> None:
                raise ValueError("Intentional failure")

            def __call__(self, **kwargs: Any) -> None:
                return self.invoke(kwargs)

        app_with_failing = GooseApp(tools=[FailingTool()])  # type: ignore[list-item]
        config = GooseConfig()
        config.goose_app = app_with_failing

        response = client.post(
            "/tooling/tools/failing_tool/invoke",
            json={"args": {}},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "Intentional failure" in data["error"]

    def test_invoke_with_empty_args(self, setup_goose_app: GooseApp) -> None:
        """Can invoke with empty args."""
        response = client.post(
            "/tooling/tools/search/invoke",
            json={},  # No args field
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
