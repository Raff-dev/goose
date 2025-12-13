"""WebSocket streaming logic for chatting conversations."""

from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import WebSocket  # type: ignore[import-not-found]
from langchain_core.messages import AIMessageChunk, ToolMessage
from starlette.websockets import WebSocketDisconnect, WebSocketState

from goose.chatting.api.schema import Conversation
from goose.chatting.store import get_store
from goose.core.config import GooseConfig
from goose.core.reload import reload_source_modules
from goose.testing.models.messages import Message, ToolCall

logger = logging.getLogger(__name__)


async def send_event(websocket: WebSocket, event_type: str, data: dict[str, Any]) -> bool:
    """Send a JSON event to the WebSocket.

    Args:
        websocket: The WebSocket connection.
        event_type: The event type (e.g., "token", "tool_call").
        data: The event data.

    Returns:
        True if sent successfully, False if connection is closed.
    """
    if websocket.client_state != WebSocketState.CONNECTED:
        return False

    try:
        await websocket.send_text(json.dumps({"type": event_type, "data": data}))
        return True
    except WebSocketDisconnect:
        return False


def _parse_args_from_string(args_str: str) -> dict[str, Any]:
    """Parse JSON args string into a dict, returning empty dict on failure."""
    if not args_str:
        return {}
    try:
        return json.loads(args_str)
    except json.JSONDecodeError:
        logger.warning("Failed to parse tool call args: %s", args_str)
        return {}


def _accumulate_tool_chunk(
    chunks: dict[int, dict[str, Any]],
    tool_chunk: dict[str, Any],
) -> None:
    """Accumulate a tool call chunk into the chunks dict."""
    idx = tool_chunk.get("index", 0)
    if idx not in chunks:
        chunks[idx] = {"name": "", "args": "", "id": ""}

    tc = chunks[idx]
    if tool_chunk.get("name"):
        tc["name"] += tool_chunk["name"]
    if tool_chunk.get("args"):
        tc["args"] += tool_chunk["args"]
    if tool_chunk.get("id"):
        tc["id"] = tool_chunk["id"]


def _build_tool_call_from_chunk(acc_tc: dict[str, Any]) -> ToolCall:
    """Build a ToolCall from an accumulated chunk."""
    return ToolCall(
        name=acc_tc.get("name", ""),
        args=_parse_args_from_string(acc_tc.get("args", "")),
        id=acc_tc.get("id"),
    )


async def stream_agent_response(
    websocket: WebSocket,
    conversation: Conversation,
    user_content: str,
) -> None:
    """Stream an agent response for the given user message.

    This function:
    1. Reloads source modules for hot-reload
    2. Builds the agent using the conversation's model
    3. Streams the response token-by-token
    4. Saves all messages to the conversation store

    Args:
        websocket: The WebSocket connection.
        conversation: The conversation to add messages to.
        user_content: The user's message content.
    """
    store = get_store()
    config = GooseConfig()
    goose_app = config.goose_app

    if goose_app is None:
        await send_event(websocket, "error", {"message": "No GooseApp configured"})
        return

    # Get agent config
    agent_config = goose_app.get_agent_config(conversation.agent_id)
    if agent_config is None:
        await send_event(websocket, "error", {"message": f"Agent not found: {conversation.agent_id}"})
        return

    # Hot-reload source modules before each message
    try:
        reload_source_modules()
    except Exception as exc:
        logger.warning("Hot-reload failed: %s", exc)

    # Re-fetch agent config after reload (function reference may have changed)
    agent_config = goose_app.get_agent_config(conversation.agent_id)
    if agent_config is None:
        await send_event(websocket, "error", {"message": "Agent not found after reload"})
        return

    # Add user message to store
    human_message = Message(type="human", content=user_content)
    store.add_message(conversation.id, human_message)

    # Echo user message back to client
    await send_event(websocket, "message", human_message.model_dump())

    # Build conversation history for the agent
    updated_conversation = store.get(conversation.id)
    if updated_conversation is None:
        await send_event(websocket, "error", {"message": "Conversation not found"})
        return

    messages = [msg.to_langchain() for msg in updated_conversation.messages]

    # Build fresh agent with the conversation's model
    try:
        agent = agent_config["get_agent"](conversation.model)
    except Exception as exc:
        logger.exception("Failed to build agent")
        await send_event(websocket, "error", {"message": f"Failed to build agent: {exc}"})
        return

    # Stream the response
    try:
        await _stream_response(websocket, agent, messages, conversation.id, store)
    except Exception as exc:
        logger.exception("Streaming failed")
        await send_event(websocket, "error", {"message": f"Streaming failed: {exc}"})


async def _stream_response(
    websocket: WebSocket,
    agent: Any,
    messages: list[Any],
    conversation_id: str,
    store: Any,
) -> None:
    """Stream the agent response and save messages."""
    accumulated_content = ""
    accumulated_tool_calls: list[ToolCall] = []
    current_tool_call_chunks: dict[int, dict[str, Any]] = {}

    for event in agent.stream({"messages": messages}, stream_mode="messages"):
        chunk, _metadata = event

        if isinstance(chunk, AIMessageChunk):
            if chunk.content:
                accumulated_content += chunk.content
                if not await send_event(websocket, "token", {"content": chunk.content}):
                    return

            # Accumulate tool call chunks (args come as partial JSON strings)
            for tool_chunk in chunk.tool_call_chunks or []:
                _accumulate_tool_chunk(current_tool_call_chunks, tool_chunk)

        elif isinstance(chunk, ToolMessage):
            # Tool is being executed - flush accumulated tool calls first
            if current_tool_call_chunks:
                # Build tool calls from accumulated chunks
                pending_tool_calls: list[ToolCall] = []
                for acc_tc in current_tool_call_chunks.values():
                    if not acc_tc.get("name"):
                        continue
                    tc = _build_tool_call_from_chunk(acc_tc)
                    pending_tool_calls.append(tc)
                    accumulated_tool_calls.append(tc)

                # Save AI message with tool_calls BEFORE tool output (required by OpenAI API)
                if pending_tool_calls or accumulated_content:
                    ai_message = Message(
                        type="ai",
                        content=accumulated_content,
                        tool_calls=pending_tool_calls,
                    )
                    store.add_message(conversation_id, ai_message)
                    accumulated_content = ""  # Reset for next AI response

                # Send tool_call events to frontend
                for tc in pending_tool_calls:
                    if not await send_event(websocket, "tool_call", tc.model_dump()):
                        return

                current_tool_call_chunks.clear()

            tool_message = Message(
                type="tool",
                content=str(chunk.content),
                tool_name=chunk.name,
                tool_call_id=getattr(chunk, "tool_call_id", None),
            )
            store.add_message(conversation_id, tool_message)

            if not await send_event(
                websocket,
                "tool_output",
                {
                    "tool_name": chunk.name,
                    "tool_call_id": getattr(chunk, "tool_call_id", None),
                    "content": str(chunk.content),
                },
            ):
                return

    # Save any remaining accumulated AI message (for responses without tool calls)
    if accumulated_content:
        ai_message = Message(
            type="ai",
            content=accumulated_content,
            tool_calls=[],
        )
        store.add_message(conversation_id, ai_message)

    await send_event(websocket, "message_end", {})


__all__ = ["stream_agent_response", "send_event"]
