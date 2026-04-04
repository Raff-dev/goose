"""Tests for chatting streaming tool error handling."""

from __future__ import annotations

import asyncio
import json
from typing import Any

from starlette.websockets import WebSocketState

from goose.chatting.api.streaming import _stream_response
from goose.chatting.store import ConversationStore


class _FakeWebSocket:
    def __init__(self) -> None:
        self.client_state = WebSocketState.CONNECTED
        self.sent_text: list[str] = []

    async def send_text(self, data: str) -> None:
        self.sent_text.append(data)


class _FakeAgent:
    def __init__(self, events: list[tuple[Any, dict[str, Any]]], exc: Exception | None = None) -> None:
        self._events = events
        self._exc = exc

    async def astream(self, _payload: dict[str, Any], stream_mode: str) -> Any:
        assert stream_mode == "messages"
        for event in self._events:
            yield event
        if self._exc is not None:
            raise self._exc


class _FakeNativeAgent:
    def __init__(self, events: list[dict[str, Any]], exc: Exception | None = None) -> None:
        self.name = "Native Agent"
        self._events = events
        self._exc = exc

    async def astream_goose(self, *, conversation: Any, messages: list[Any]) -> Any:
        assert conversation.id
        assert isinstance(messages, list)
        for event in self._events:
            yield event
        if self._exc is not None:
            raise self._exc


def _extract_event_types(sent_text: list[str]) -> list[str]:
    types: list[str] = []
    for raw in sent_text:
        data = json.loads(raw)
        types.append(data["type"])
    return types


def _extract_message_types(sent_text: list[str]) -> list[str]:
    message_types: list[str] = []
    for raw in sent_text:
        data = json.loads(raw)
        if data["type"] != "message":
            continue
        message_types.append(data["data"].get("type", ""))
    return message_types


class TestToolFailuresAreInBand:
    def test_flushes_tool_call_then_emits_error_message(self) -> None:
        from langchain_core.messages import AIMessageChunk

        store = ConversationStore()
        conv = store.create(agent_id="a1", agent_name="Agent")

        # Simulate agent emitting a tool call chunk, then crashing before tool output.
        chunk = AIMessageChunk(
            content="",
            tool_call_chunks=[
                {
                    "index": 0,
                    "name": "trigger_system_fault",
                    "args": '{"foo": 1}',
                    "id": "call_1",
                }
            ],
        )

        websocket = _FakeWebSocket()
        agent = _FakeAgent(events=[(chunk, {})], exc=RuntimeError("boom"))

        asyncio.run(_stream_response(websocket, agent, [], conv.id, store))

        event_types = _extract_event_types(websocket.sent_text)
        assert "tool_call" in event_types
        assert event_types[-1] == "message_end"

        message_types = _extract_message_types(websocket.sent_text)
        assert "error" in message_types

        updated = store.get(conv.id)
        assert updated is not None
        assert any(m.type == "ai" and m.tool_calls for m in updated.messages)
        assert any(m.type == "tool" and m.tool_call_id == "call_1" for m in updated.messages)
        assert any(m.type == "error" for m in updated.messages)


class TestNativeChatProtocol:
    def test_updates_metadata_and_persists_streamed_messages(self) -> None:
        store = ConversationStore()
        conv = store.create(agent_id="a1", agent_name="Agent")

        websocket = _FakeWebSocket()
        agent = _FakeNativeAgent(
            events=[
                {"type": "conversation_meta", "data": {"callwise_conversation_id": "cw-123"}},
                {"type": "tool_call", "data": {"name": "list_calls", "args": {"limit": 5}, "id": "call_1"}},
                {
                    "type": "tool_output",
                    "data": {"tool_name": "list_calls", "content": "returned 5 calls", "tool_call_id": "call_1"},
                },
                {"type": "token", "data": {"content": "Done."}},
                {"type": "message_end", "data": {}},
            ]
        )

        asyncio.run(_stream_response(websocket, agent, [], conv.id, store))

        updated = store.get(conv.id)
        assert updated is not None
        assert updated.metadata["callwise_conversation_id"] == "cw-123"
        assert any(m.type == "ai" and m.tool_calls for m in updated.messages)
        assert any(m.type == "tool" and m.tool_name == "list_calls" for m in updated.messages)
        assert any(m.type == "ai" and m.content == "Done." for m in updated.messages)

        event_types = _extract_event_types(websocket.sent_text)
        assert event_types == ["tool_call", "tool_output", "token", "message_end"]

    def test_native_protocol_surfaces_exceptions_in_band(self) -> None:
        store = ConversationStore()
        conv = store.create(agent_id="a1", agent_name="Agent")

        websocket = _FakeWebSocket()
        agent = _FakeNativeAgent(events=[], exc=RuntimeError("native boom"))

        asyncio.run(_stream_response(websocket, agent, [], conv.id, store))

        event_types = _extract_event_types(websocket.sent_text)
        assert event_types == ["message", "message_end"]

        updated = store.get(conv.id)
        assert updated is not None
        assert any(m.type == "error" and m.content == "native boom" for m in updated.messages)
