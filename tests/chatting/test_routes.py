"""Tests for chatting API routes."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from goose.app import app
from goose.chatting.store import reset_store
from goose.core.app import GooseApp
from goose.core.config import GooseConfig


def sample_get_agent(model: str) -> str:
    """Sample agent factory for testing."""
    return f"agent-{model}"


@pytest.fixture(autouse=True)
def reset_config() -> None:
    """Reset config and store before each test."""
    GooseConfig.reset()
    reset_store()


@pytest.fixture
def client() -> TestClient:
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def config_with_agents() -> GooseConfig:
    """Configure GooseApp with test agents."""
    config = GooseConfig()
    config.goose_app = GooseApp(
        agents=[
            {
                "name": "Test Agent",
                "get_agent": sample_get_agent,
                "models": ["gpt-4o-mini", "gpt-4o"],
            },
            {
                "name": "Another Agent",
                "get_agent": sample_get_agent,
                "models": ["gpt-4o"],
            },
        ],
    )
    return config


class TestListAgents:
    """Tests for GET /chatting/agents."""

    def test_returns_empty_when_no_app(self, client: TestClient) -> None:
        """Returns empty list when no GooseApp configured."""
        response = client.get("/chatting/agents")

        assert response.status_code == 200
        assert response.json() == []

    def test_returns_agents_with_ids(self, client: TestClient, config_with_agents: GooseConfig) -> None:
        """Returns agent summaries with IDs."""
        response = client.get("/chatting/agents")

        assert response.status_code == 200
        agents = response.json()
        assert len(agents) == 2

        agent = agents[0]
        assert "id" in agent
        assert agent["name"] == "Test Agent"
        assert agent["models"] == ["gpt-4o-mini", "gpt-4o"]


class TestGetAgent:
    """Tests for GET /chatting/agents/{agent_id}."""

    def test_returns_agent_by_id(self, client: TestClient, config_with_agents: GooseConfig) -> None:
        """Returns agent details by ID."""
        # Get agents first to get the ID
        agents_response = client.get("/chatting/agents")
        agent_id = agents_response.json()[0]["id"]

        response = client.get(f"/chatting/agents/{agent_id}")

        assert response.status_code == 200
        agent = response.json()
        assert agent["id"] == agent_id
        assert agent["name"] == "Test Agent"

    def test_returns_404_for_unknown_id(self, client: TestClient, config_with_agents: GooseConfig) -> None:
        """Returns 404 for unknown agent ID."""
        response = client.get("/chatting/agents/unknown-id")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestListConversations:
    """Tests for GET /chatting/conversations."""

    def test_returns_empty_list(self, client: TestClient) -> None:
        """Returns empty list when no conversations."""
        response = client.get("/chatting/conversations")

        assert response.status_code == 200
        assert response.json() == []


class TestCreateConversation:
    """Tests for POST /chatting/conversations."""

    def test_creates_conversation(self, client: TestClient, config_with_agents: GooseConfig) -> None:
        """Creates a new conversation."""
        agents_response = client.get("/chatting/agents")
        agent_id = agents_response.json()[0]["id"]

        response = client.post(
            "/chatting/conversations",
            json={
                "agent_id": agent_id,
                "model": "gpt-4o-mini",
                "title": "Test Chat",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["agent_id"] == agent_id
        assert data["agent_name"] == "Test Agent"
        assert data["model"] == "gpt-4o-mini"
        assert data["title"] == "Test Chat"

    def test_creates_with_default_title(self, client: TestClient, config_with_agents: GooseConfig) -> None:
        """Creates conversation with default title."""
        agents_response = client.get("/chatting/agents")
        agent_id = agents_response.json()[0]["id"]

        response = client.post(
            "/chatting/conversations",
            json={
                "agent_id": agent_id,
                "model": "gpt-4o-mini",
            },
        )

        assert response.status_code == 201
        assert response.json()["title"] == "New conversation"

    def test_rejects_unknown_agent(self, client: TestClient, config_with_agents: GooseConfig) -> None:
        """Rejects unknown agent ID."""
        response = client.post(
            "/chatting/conversations",
            json={
                "agent_id": "unknown-agent",
                "model": "gpt-4o-mini",
            },
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_rejects_unavailable_model(self, client: TestClient, config_with_agents: GooseConfig) -> None:
        """Rejects model not available for agent."""
        agents_response = client.get("/chatting/agents")
        agent_id = agents_response.json()[1]["id"]  # Another Agent - only has gpt-4o

        response = client.post(
            "/chatting/conversations",
            json={
                "agent_id": agent_id,
                "model": "gpt-4o-mini",  # Not available for this agent
            },
        )

        assert response.status_code == 400
        assert "not available" in response.json()["detail"].lower()


class TestGetConversation:
    """Tests for GET /chatting/conversations/{id}."""

    def test_returns_conversation(self, client: TestClient, config_with_agents: GooseConfig) -> None:
        """Returns conversation with messages."""
        agents_response = client.get("/chatting/agents")
        agent_id = agents_response.json()[0]["id"]

        create_response = client.post(
            "/chatting/conversations",
            json={"agent_id": agent_id, "model": "gpt-4o-mini"},
        )
        conversation_id = create_response.json()["id"]

        response = client.get(f"/chatting/conversations/{conversation_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == conversation_id
        assert data["messages"] == []

    def test_returns_404_for_unknown(self, client: TestClient) -> None:
        """Returns 404 for unknown conversation."""
        response = client.get("/chatting/conversations/unknown-id")

        assert response.status_code == 404


class TestDeleteConversation:
    """Tests for DELETE /chatting/conversations/{id}."""

    def test_deletes_conversation(self, client: TestClient, config_with_agents: GooseConfig) -> None:
        """Deletes an existing conversation."""
        agents_response = client.get("/chatting/agents")
        agent_id = agents_response.json()[0]["id"]

        create_response = client.post(
            "/chatting/conversations",
            json={"agent_id": agent_id, "model": "gpt-4o-mini"},
        )
        conversation_id = create_response.json()["id"]

        response = client.delete(f"/chatting/conversations/{conversation_id}")

        assert response.status_code == 204

        # Verify it's gone
        get_response = client.get(f"/chatting/conversations/{conversation_id}")
        assert get_response.status_code == 404

    def test_returns_404_for_unknown(self, client: TestClient) -> None:
        """Returns 404 for unknown conversation."""
        response = client.delete("/chatting/conversations/unknown-id")

        assert response.status_code == 404


class TestConversationWebSocket:
    """Tests for WebSocket /chatting/ws/conversations/{id}."""

    def test_rejects_unknown_conversation(self, client: TestClient) -> None:
        """WebSocket closes with error for unknown conversation."""
        with pytest.raises(Exception):  # WebSocket rejection
            with client.websocket_connect("/chatting/ws/conversations/unknown-id"):
                pass

    def test_accepts_valid_conversation(self, client: TestClient, config_with_agents: GooseConfig) -> None:
        """WebSocket accepts connection for valid conversation."""
        # Create a conversation
        agents_response = client.get("/chatting/agents")
        agent_id = agents_response.json()[0]["id"]

        create_response = client.post(
            "/chatting/conversations",
            json={"agent_id": agent_id, "model": "gpt-4o-mini"},
        )
        conversation_id = create_response.json()["id"]

        # Connect to WebSocket
        with client.websocket_connect(f"/chatting/ws/conversations/{conversation_id}") as websocket:
            # Just verify we can connect - we'd need a mock agent to fully test streaming
            websocket.close()
