"""WebSocket streaming logic for chatting conversations."""

from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import WebSocket  # type: ignore[import-not-found]
from langchain_core.messages import AIMessageChunk, ToolMessage
from starlette.websockets import WebSocketDisconnect, WebSocketState

from goose.chatting.agent_protocol import GooseAgentEvent, supports_goose_chat_protocol
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


def _build_tool_call_from_event(data: dict[str, Any]) -> ToolCall:
    """Build a ToolCall from a Goose-native event payload."""
    raw_name = str(data.get("name") or "").strip()
    if not raw_name:
        raise ValueError("Goose-native tool_call event must include a tool name")

    raw_args = data.get("args")
    args = raw_args if isinstance(raw_args, dict) else {}

    raw_id = data.get("id")
    tool_call_id = str(raw_id) if raw_id is not None else None

    return ToolCall(name=raw_name, args=args, id=tool_call_id)


def _coerce_goose_event(raw_event: GooseAgentEvent | dict[str, Any]) -> GooseAgentEvent:
    """Normalize a Goose-native event from model or plain dict input."""
    if isinstance(raw_event, GooseAgentEvent):
        return raw_event
    if isinstance(raw_event, dict):
        return GooseAgentEvent.model_validate(raw_event)
    raise TypeError(f"Unsupported Goose-native event type: {type(raw_event).__name__}")


async def _emit_in_band_error(
    websocket: WebSocket,
    *,
    conversation_id: str,
    store: Any,
    message: str,
) -> None:
    """Persist and emit a terminal in-band error message."""
    error_message = Message(type="error", content=message)
    store.add_message(conversation_id, error_message)
    await send_event(websocket, "message", error_message.model_dump())
    await send_event(websocket, "message_end", {})


async def _emit_tool_output(
    websocket: WebSocket,
    *,
    conversation_id: str,
    store: Any,
    data: dict[str, Any],
) -> bool:
    """Persist and emit a Goose-native tool output event."""
    tool_name = str(data.get("tool_name") or data.get("name") or "unknown")
    tool_call_id = data.get("tool_call_id") or data.get("id")
    tool_message = Message(
        type="tool",
        content=str(data.get("content") or ""),
        tool_name=tool_name,
        tool_call_id=str(tool_call_id) if tool_call_id is not None else None,
    )
    store.add_message(conversation_id, tool_message)
    return await send_event(
        websocket,
        "tool_output",
        {
            "tool_name": tool_message.tool_name,
            "tool_call_id": tool_message.tool_call_id,
            "content": tool_message.content,
        },
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

    messages = list(updated_conversation.messages)

    # Get the pre-built agent from config
    agent = agent_config["agent"]
    if agent is None:
        await send_event(websocket, "error", {"message": "Agent not configured"})
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
    messages: list[Message],
    conversation_id: str,
    store: Any,
) -> None:
    """Dispatch streaming to Goose-native or legacy LangChain agents."""
    if supports_goose_chat_protocol(agent):
        conversation = store.get(conversation_id)
        if conversation is None:
            raise ValueError("Conversation not found")
        await _stream_goose_response(
            websocket=websocket,
            agent=agent,
            messages=messages,
            conversation=conversation,
            conversation_id=conversation_id,
            store=store,
        )
        return

    langchain_messages = [msg.to_langchain() for msg in messages]
    await _stream_langchain_response(websocket, agent, langchain_messages, conversation_id, store)


async def _stream_goose_response(
    *,
    websocket: WebSocket,
    agent: Any,
    messages: list[Message],
    conversation: Conversation,
    conversation_id: str,
    store: Any,
) -> None:
    """Stream a response from a Goose-native chat agent."""
    accumulated_content = ""

    try:
        async for raw_event in agent.astream_goose(conversation=conversation, messages=messages):
            event = _coerce_goose_event(raw_event)
            data = dict(event.data)

            if event.type == "conversation_meta":
                store.update_metadata(conversation_id, data)
                continue

            if event.type == "message":
                message = Message.model_validate(data)
                store.add_message(conversation_id, message)
                if not await send_event(websocket, "message", message.model_dump()):
                    return
                continue

            if event.type == "token":
                content = str(data.get("content") or "")
                if not content:
                    continue
                accumulated_content += content
                if not await send_event(websocket, "token", {"content": content}):
                    return
                continue

            if event.type == "tool_call":
                tool_call = _build_tool_call_from_event(data)
                store.add_message(
                    conversation_id,
                    Message(type="ai", content=accumulated_content, tool_calls=[tool_call]),
                )
                accumulated_content = ""
                if not await send_event(websocket, "tool_call", tool_call.model_dump()):
                    return
                continue

            if event.type == "tool_output":
                accumulated_content = ""
                if not await _emit_tool_output(
                    websocket,
                    conversation_id=conversation_id,
                    store=store,
                    data=data,
                ):
                    return
                continue

            if event.type == "error":
                await _emit_in_band_error(
                    websocket,
                    conversation_id=conversation_id,
                    store=store,
                    message=str(data.get("message") or "Unknown error"),
                )
                return

            if event.type == "message_end":
                break
    except Exception as exc:
        logger.exception("Goose-native streaming failed")
        await _emit_in_band_error(
            websocket,
            conversation_id=conversation_id,
            store=store,
            message=str(exc),
        )
        return

    if accumulated_content:
        ai_message = Message(type="ai", content=accumulated_content, tool_calls=[])
        store.add_message(conversation_id, ai_message)

    await send_event(websocket, "message_end", {})


async def _stream_langchain_response(
    websocket: WebSocket,
    agent: Any,
    messages: list[Any],
    conversation_id: str,
    store: Any,
) -> None:
    """Stream the agent response and save messages."""
    accumulated_content = ""
    current_tool_call_chunks: dict[int, dict[str, Any]] = {}

    async def _flush_pending_tool_calls() -> tuple[bool, list[ToolCall]]:
        if not current_tool_call_chunks:
            return True, []

        pending_tool_calls: list[ToolCall] = []
        for acc_tc in current_tool_call_chunks.values():
            if not acc_tc.get("name"):
                continue
            tc = _build_tool_call_from_chunk(acc_tc)
            pending_tool_calls.append(tc)

        if pending_tool_calls or accumulated_content:
            ai_message = Message(
                type="ai",
                content=accumulated_content,
                tool_calls=pending_tool_calls,
            )
            store.add_message(conversation_id, ai_message)

        for tc in pending_tool_calls:
            if not await send_event(websocket, "tool_call", tc.model_dump()):
                return False, pending_tool_calls

        current_tool_call_chunks.clear()
        return True, pending_tool_calls

    saw_tool_calls = False

    try:
        async for event in agent.astream({"messages": messages}, stream_mode="messages"):
            chunk, _metadata = event

            if isinstance(chunk, AIMessageChunk):
                if chunk.content:
                    accumulated_content += chunk.content
                    if not await send_event(websocket, "token", {"content": chunk.content}):
                        return

                for tool_chunk in chunk.tool_call_chunks or []:
                    saw_tool_calls = True
                    _accumulate_tool_chunk(current_tool_call_chunks, tool_chunk)

            elif isinstance(chunk, ToolMessage):
                saw_tool_calls = True
                ok, _pending_tool_calls = await _flush_pending_tool_calls()
                if not ok:
                    return
                accumulated_content = ""

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
    except Exception as exc:
        if saw_tool_calls or current_tool_call_chunks:
            ok, pending_tool_calls = await _flush_pending_tool_calls()
            if not ok:
                return
            accumulated_content = ""

            # If the agent crashed after emitting tool_calls but before producing tool outputs,
            # persist a tool response for each tool_call_id to keep the tool-call protocol valid.
            for tc in pending_tool_calls:
                if not tc.id:
                    continue
                tool_message = Message(
                    type="tool",
                    content=str(exc),
                    tool_name=tc.name,
                    tool_call_id=tc.id,
                )
                store.add_message(conversation_id, tool_message)

            error_message = Message(type="error", content=str(exc))
            store.add_message(conversation_id, error_message)
            await send_event(websocket, "message", error_message.model_dump())
            await send_event(websocket, "message_end", {})
            return
        raise

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
