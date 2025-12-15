"""In-memory conversation storage for chatting module."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from goose.chatting.api.schema import Conversation, ConversationSummary
from goose.testing.models.messages import Message


class ConversationStore:
    """In-memory storage for conversations.

    Conversations are stored in runtime memory only and lost on restart.
    This is intentional - the chatting feature is for interactive exploration,
    not persistent history.
    """

    def __init__(self) -> None:
        self._conversations: dict[str, dict[str, Any]] = {}
        self._next_id = 1

    def create(self, agent_id: str, agent_name: str, title: str | None = None) -> Conversation:
        """Create a new conversation.

        Args:
            agent_id: ID of the agent to chat with.
            agent_name: Display name of the agent (denormalized).
            title: Optional title. Auto-generated if not provided.

        Returns:
            The created conversation.
        """
        conversation_id = str(self._next_id)
        self._next_id += 1
        now = datetime.now(timezone.utc)

        conversation_data = {
            "id": conversation_id,
            "agent_id": agent_id,
            "agent_name": agent_name,
            "title": title or "New conversation",
            "messages": [],
            "created_at": now,
            "updated_at": now,
        }
        self._conversations[conversation_id] = conversation_data

        return Conversation(**conversation_data)

    def get(self, conversation_id: str) -> Conversation | None:
        """Get a conversation by ID.

        Args:
            conversation_id: ID of the conversation.

        Returns:
            The conversation if found, None otherwise.
        """
        data = self._conversations.get(conversation_id)
        if data is None:
            return None
        return Conversation(**data)

    def list_all(self) -> list[ConversationSummary]:
        """List all conversations as summaries.

        Returns:
            List of conversation summaries, newest first.
        """
        summaries = [
            ConversationSummary(
                id=data["id"],
                agent_id=data["agent_id"],
                agent_name=data["agent_name"],
                title=data["title"],
                message_count=len(data["messages"]),
                created_at=data["created_at"],
                updated_at=data["updated_at"],
            )
            for data in self._conversations.values()
        ]
        return sorted(summaries, key=lambda c: c.updated_at, reverse=True)

    def delete(self, conversation_id: str) -> bool:
        """Delete a conversation.

        Args:
            conversation_id: ID of the conversation to delete.

        Returns:
            True if deleted, False if not found.
        """
        if conversation_id in self._conversations:
            del self._conversations[conversation_id]
            return True
        return False

    def add_message(self, conversation_id: str, message: Message) -> bool:
        """Add a message to a conversation.

        Args:
            conversation_id: ID of the conversation.
            message: The message to add.

        Returns:
            True if added, False if conversation not found.
        """
        data = self._conversations.get(conversation_id)
        if data is None:
            return False

        data["messages"].append(message.model_dump())
        data["updated_at"] = datetime.now(timezone.utc)

        # Auto-update title from first human message if still default
        if data["title"] == "New conversation" and message.type == "human":
            # Truncate to first 50 chars
            content = message.content[:50]
            if len(message.content) > 50:
                content += "..."
            data["title"] = content

        return True

    def update_title(self, conversation_id: str, title: str) -> bool:
        """Update a conversation's title.

        Args:
            conversation_id: ID of the conversation.
            title: New title.

        Returns:
            True if updated, False if not found.
        """
        data = self._conversations.get(conversation_id)
        if data is None:
            return False

        data["title"] = title
        data["updated_at"] = datetime.now(timezone.utc)
        return True

    def clear(self) -> None:
        """Clear all conversations."""
        self._conversations.clear()


class _StoreHolder:
    """Holder for the global store instance to avoid global statements."""

    instance: ConversationStore | None = None


def get_store() -> ConversationStore:
    """Get the global conversation store instance."""
    if _StoreHolder.instance is None:
        _StoreHolder.instance = ConversationStore()
    return _StoreHolder.instance


def reset_store() -> None:
    """Reset the global store (for testing)."""
    _StoreHolder.instance = None


__all__ = ["ConversationStore", "get_store", "reset_store"]
