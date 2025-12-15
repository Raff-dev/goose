"""FastAPI router for chatting endpoints."""

from __future__ import annotations

import json
import logging

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect  # type: ignore[import-not-found]

from goose.chatting.api.schema import (
    AgentSummary,
    Conversation,
    ConversationSummary,
    CreateConversationRequest,
    CreateConversationResponse,
)
from goose.chatting.api.streaming import send_event, stream_agent_response
from goose.chatting.store import get_store
from goose.core.config import GooseConfig

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/agents", response_model=list[AgentSummary])
def list_agents() -> list[AgentSummary]:
    """List all configured agents available for chatting."""
    config = GooseConfig()
    goose_app = config.goose_app

    if goose_app is None:
        return []

    return [
        AgentSummary(
            id=agent["id"],
            name=agent["name"],
        )
        for agent in goose_app.agents
    ]


@router.get("/agents/{agent_id}", response_model=AgentSummary)
def get_agent(agent_id: str) -> AgentSummary:
    """Get a specific agent by ID."""
    config = GooseConfig()
    goose_app = config.goose_app

    if goose_app is None:
        raise HTTPException(status_code=404, detail="No GooseApp configured")

    agent_config = goose_app.get_agent_config(agent_id)
    if agent_config is None:
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")

    return AgentSummary(
        id=agent_config["id"],
        name=agent_config["name"],
    )


@router.get("/conversations", response_model=list[ConversationSummary])
def list_conversations() -> list[ConversationSummary]:
    """List all conversations."""
    store = get_store()
    return store.list_all()


@router.post("/conversations", response_model=CreateConversationResponse, status_code=201)
def create_conversation(request: CreateConversationRequest) -> CreateConversationResponse:
    """Create a new conversation."""
    config = GooseConfig()
    goose_app = config.goose_app

    if goose_app is None:
        raise HTTPException(status_code=400, detail="No GooseApp configured")

    # Validate agent exists
    agent_config = goose_app.get_agent_config(request.agent_id)
    if agent_config is None:
        raise HTTPException(status_code=404, detail=f"Agent not found: {request.agent_id}")

    store = get_store()
    conversation = store.create(
        agent_id=request.agent_id,
        agent_name=agent_config["name"],
        title=request.title,
    )

    return CreateConversationResponse(
        id=conversation.id,
        agent_id=conversation.agent_id,
        agent_name=conversation.agent_name,
        title=conversation.title,
        created_at=conversation.created_at,
    )


@router.get("/conversations/{conversation_id}", response_model=Conversation)
def get_conversation(conversation_id: str) -> Conversation:
    """Get a conversation with all messages."""
    store = get_store()
    conversation = store.get(conversation_id)

    if conversation is None:
        raise HTTPException(status_code=404, detail=f"Conversation not found: {conversation_id}")

    return conversation


@router.delete("/conversations/{conversation_id}", status_code=204)
def delete_conversation(conversation_id: str) -> None:
    """Delete a conversation."""
    store = get_store()
    deleted = store.delete(conversation_id)

    if not deleted:
        raise HTTPException(status_code=404, detail=f"Conversation not found: {conversation_id}")


@router.websocket("/ws/conversations/{conversation_id}")
async def conversation_websocket(websocket: WebSocket, conversation_id: str) -> None:
    """WebSocket endpoint for streaming chat messages.

    Client sends: {"type": "send_message", "content": "..."}
    Server sends: {"type": "token|tool_call|tool_output|message|message_end|error", "data": {...}}
    """
    store = get_store()
    conversation = store.get(conversation_id)

    if conversation is None:
        await websocket.close(code=4004, reason="Conversation not found")
        return

    await websocket.accept()

    try:
        while True:
            # Wait for client message
            raw_message = await websocket.receive_text()

            try:
                message = json.loads(raw_message)
            except json.JSONDecodeError:
                await send_event(websocket, "error", {"message": "Invalid JSON"})
                continue

            msg_type = message.get("type")
            if msg_type != "send_message":
                await send_event(websocket, "error", {"message": f"Unknown message type: {msg_type}"})
                continue

            content = message.get("content", "").strip()
            if not content:
                await send_event(websocket, "error", {"message": "Empty message content"})
                continue

            # Re-fetch conversation in case it was modified
            conversation = store.get(conversation_id)
            if conversation is None:
                await send_event(websocket, "error", {"message": "Conversation not found"})
                break

            # Stream the agent response
            await stream_agent_response(websocket, conversation, content)

    except WebSocketDisconnect:
        logger.debug("WebSocket disconnected for conversation %s", conversation_id)
    except Exception as exc:
        logger.exception("WebSocket error for conversation %s", conversation_id)
        try:
            await send_event(websocket, "error", {"message": str(exc)})
        except Exception:  # nosec B110
            pass


__all__ = ["router"]
