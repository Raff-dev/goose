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
