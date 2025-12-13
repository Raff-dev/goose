"""Tests for conversation store."""

from __future__ import annotations

import pytest

from goose.chatting.store import ConversationStore, get_store, reset_store
from goose.testing.models.messages import Message


@pytest.fixture(autouse=True)
def clean_store() -> None:
    """Reset the global store before each test."""
    reset_store()


class TestConversationStore:
    """Tests for ConversationStore class."""

    def test_create_conversation(self) -> None:
        """Can create a conversation with required fields."""
        store = ConversationStore()
        conversation = store.create(
            agent_id="agent-123",
            agent_name="Test Agent",
            model="gpt-4o-mini",
            title="Test Chat",
        )

        assert conversation.id == "1"  # Sequential ID
        assert conversation.agent_id == "agent-123"
        assert conversation.agent_name == "Test Agent"
        assert conversation.model == "gpt-4o-mini"
        assert conversation.title == "Test Chat"
        assert conversation.messages == []
        assert conversation.created_at is not None
        assert conversation.updated_at is not None

    def test_create_with_default_title(self) -> None:
        """Creates default title when not provided."""
        store = ConversationStore()
        conversation = store.create(
            agent_id="agent-123",
            agent_name="Test Agent",
            model="gpt-4o-mini",
        )

        assert conversation.title == "New conversation"
        assert conversation.id == "1"

    def test_create_multiple_conversations_sequential_ids(self) -> None:
        """Creates sequential IDs for multiple conversations."""
        store = ConversationStore()
        conv1 = store.create(
            agent_id="agent-123",
            agent_name="Test Agent",
            model="gpt-4o-mini",
        )
        conv2 = store.create(
            agent_id="agent-123",
            agent_name="Test Agent",
            model="gpt-4o-mini",
        )
        conv3 = store.create(
            agent_id="agent-123",
            agent_name="Test Agent",
            model="gpt-4o-mini",
        )

        assert conv1.id == "1"
        assert conv2.id == "2"
        assert conv3.id == "3"

    def test_get_existing_conversation(self) -> None:
        """Can retrieve an existing conversation."""
        store = ConversationStore()
        created = store.create(
            agent_id="agent-123",
            agent_name="Test Agent",
            model="gpt-4o-mini",
        )

        fetched = store.get(created.id)

        assert fetched is not None
        assert fetched.id == created.id
        assert fetched.agent_id == created.agent_id

    def test_get_returns_none_for_unknown(self) -> None:
        """Returns None for unknown conversation ID."""
        store = ConversationStore()

        assert store.get("unknown-id") is None

    def test_list_all_returns_summaries(self) -> None:
        """List returns conversation summaries."""
        store = ConversationStore()
        store.create(agent_id="a1", agent_name="Agent 1", model="m1", title="Chat 1")
        store.create(agent_id="a2", agent_name="Agent 2", model="m2", title="Chat 2")

        summaries = store.list_all()

        assert len(summaries) == 2
        # Newest first
        assert summaries[0].title == "Chat 2"
        assert summaries[1].title == "Chat 1"

    def test_list_all_empty(self) -> None:
        """List returns empty list when no conversations."""
        store = ConversationStore()

        assert store.list_all() == []

    def test_delete_existing(self) -> None:
        """Can delete an existing conversation."""
        store = ConversationStore()
        created = store.create(agent_id="a1", agent_name="Agent", model="m1")

        result = store.delete(created.id)

        assert result is True
        assert store.get(created.id) is None

    def test_delete_unknown_returns_false(self) -> None:
        """Deleting unknown ID returns False."""
        store = ConversationStore()

        assert store.delete("unknown-id") is False

    def test_add_message(self) -> None:
        """Can add messages to a conversation."""
        store = ConversationStore()
        created = store.create(agent_id="a1", agent_name="Agent", model="m1")

        message = Message(type="human", content="Hello")
        result = store.add_message(created.id, message)

        assert result is True
        fetched = store.get(created.id)
        assert fetched is not None
        assert len(fetched.messages) == 1
        assert fetched.messages[0].content == "Hello"

    def test_add_message_updates_timestamp(self) -> None:
        """Adding message updates updated_at."""
        store = ConversationStore()
        created = store.create(agent_id="a1", agent_name="Agent", model="m1")
        original_updated = created.updated_at

        message = Message(type="human", content="Hello")
        store.add_message(created.id, message)

        fetched = store.get(created.id)
        assert fetched is not None
        assert fetched.updated_at >= original_updated

    def test_add_message_to_unknown_returns_false(self) -> None:
        """Adding message to unknown conversation returns False."""
        store = ConversationStore()
        message = Message(type="human", content="Hello")

        assert store.add_message("unknown-id", message) is False

    def test_auto_title_from_first_human_message(self) -> None:
        """Title auto-updates from first human message."""
        store = ConversationStore()
        created = store.create(agent_id="a1", agent_name="Agent", model="m1")
        assert created.title == "New conversation"

        message = Message(type="human", content="What is the weather today?")
        store.add_message(created.id, message)

        fetched = store.get(created.id)
        assert fetched is not None
        assert fetched.title == "What is the weather today?"

    def test_auto_title_truncates_long_content(self) -> None:
        """Long messages are truncated for title."""
        store = ConversationStore()
        created = store.create(agent_id="a1", agent_name="Agent", model="m1")

        long_content = "A" * 100
        message = Message(type="human", content=long_content)
        store.add_message(created.id, message)

        fetched = store.get(created.id)
        assert fetched is not None
        assert len(fetched.title) == 53  # 50 chars + "..."
        assert fetched.title.endswith("...")

    def test_clear_removes_all(self) -> None:
        """Clear removes all conversations."""
        store = ConversationStore()
        store.create(agent_id="a1", agent_name="Agent 1", model="m1")
        store.create(agent_id="a2", agent_name="Agent 2", model="m2")

        store.clear()

        assert store.list_all() == []


class TestGlobalStore:
    """Tests for global store singleton."""

    def test_get_store_returns_same_instance(self) -> None:
        """get_store returns the same instance."""
        store1 = get_store()
        store2 = get_store()

        assert store1 is store2

    def test_reset_store_creates_new_instance(self) -> None:
        """reset_store creates a new instance on next get."""
        store1 = get_store()
        reset_store()
        store2 = get_store()

        assert store1 is not store2
