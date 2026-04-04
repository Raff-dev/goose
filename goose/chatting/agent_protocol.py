"""Framework-agnostic chat agent protocol for Goose."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any, Literal, Protocol, runtime_checkable

from pydantic import BaseModel, Field

from goose.chatting.api.schema import Conversation
from goose.testing.models.messages import Message

GooseAgentEventType = Literal[
    "message",
    "token",
    "tool_call",
    "tool_output",
    "message_end",
    "error",
    "conversation_meta",
]


class GooseAgentEvent(BaseModel):
    """Single event emitted by a Goose-native chat agent."""

    type: GooseAgentEventType
    data: dict[str, Any] = Field(default_factory=dict)


@runtime_checkable
class GooseChatAgent(Protocol):
    """Protocol for chat agents that stream Goose-native events."""

    name: str

    def astream_goose(
        self,
        *,
        conversation: Conversation,
        messages: list[Message],
    ) -> AsyncIterator[GooseAgentEvent]:
        """Yield Goose-native chat events for one assistant turn."""


def supports_goose_chat_protocol(agent: object) -> bool:
    """Return True when an agent exposes the Goose-native streaming API."""

    return callable(getattr(agent, "astream_goose", None))


__all__ = [
    "GooseAgentEvent",
    "GooseAgentEventType",
    "GooseChatAgent",
    "supports_goose_chat_protocol",
]
