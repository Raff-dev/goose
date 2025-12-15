"""Pydantic schemas for chatting API requests and responses."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from goose.testing.models.messages import Message


class AgentSummary(BaseModel):
    """Agent available for chatting."""

    id: str
    name: str


class ConversationSummary(BaseModel):
    """Summary of a conversation for listing."""

    id: str
    agent_id: str
    agent_name: str
    title: str
    message_count: int
    created_at: datetime
    updated_at: datetime


class Conversation(BaseModel):
    """Full conversation with messages."""

    id: str
    agent_id: str
    agent_name: str
    title: str
    messages: list[Message] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class CreateConversationRequest(BaseModel):
    """Request to create a new conversation."""

    agent_id: str
    title: str | None = None


class CreateConversationResponse(BaseModel):
    """Response after creating a conversation."""

    id: str
    agent_id: str
    agent_name: str
    title: str
    created_at: datetime


class SendMessageRequest(BaseModel):
    """Request to send a message to the agent (via WebSocket)."""

    content: str


class StreamEvent(BaseModel):
    """WebSocket event for streaming."""

    type: str  # "token", "tool_call", "tool_output", "message_end", "error"
    data: dict[str, Any] = Field(default_factory=dict)


__all__ = [
    "AgentSummary",
    "ConversationSummary",
    "Conversation",
    "CreateConversationRequest",
    "CreateConversationResponse",
    "SendMessageRequest",
    "StreamEvent",
]
