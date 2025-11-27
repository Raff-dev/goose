"""Pydantic models for structured agent responses and tool calls."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ToolCall(BaseModel):
    """Represents a single tool invocation initiated by the agent."""

    name: str
    args: dict[str, Any] = Field(default_factory=dict)
    id: str | None = None


class Message(BaseModel):
    """Represents a conversational message exchanged with the agent."""

    type: str
    content: str = ""
    tool_calls: list[ToolCall] = Field(default_factory=list)
    tool_name: str | None = None

    @classmethod
    def from_langchain_message(cls, message: Any) -> Message:
        """Convert a LangChain message into the internal Message representation."""
        msg_type = type(message).__name__.lower().replace("message", "")

        match msg_type:
            case "human":
                return cls(type="human", content=str(getattr(message, "content", "")))
            case "ai":
                content = str(getattr(message, "content", ""))
                tool_calls_raw = getattr(message, "tool_calls", [])
                tool_calls = [
                    ToolCall(
                        name=tool_call.get("name", "unknown"),
                        args=tool_call.get("args", {}),
                        id=tool_call.get("id"),
                    )
                    for tool_call in tool_calls_raw
                ]
                return cls(type="ai", content=content, tool_calls=tool_calls)
            case "tool":
                content = str(getattr(message, "content", ""))
                tool_name = getattr(message, "name", "unknown")
                return cls(type="tool", content=content, tool_name=tool_name)
            case _:
                return cls(type=msg_type, content=str(message))


class AgentResponse(BaseModel):
    """Structured representation of an agent query response."""

    messages: list[Message] = Field(default_factory=list)

    @classmethod
    def from_langchain(cls, response_dict: dict[str, Any]) -> AgentResponse:
        """Create an AgentResponse from the raw agent.query response payload."""
        raw_messages = response_dict.get("messages", [])
        messages = [Message.from_langchain_message(msg) for msg in raw_messages]
        return cls(messages=messages)

    @property
    def tool_calls(self) -> list[ToolCall]:
        """Return all tool calls made during the conversation."""
        tool_calls: list[ToolCall] = []
        for message in self.messages:
            tool_calls.extend(message.tool_calls)
        return tool_calls

    @property
    def tool_call_names(self) -> list[str]:
        """Return the ordered list of tool call names."""
        return [tool_call.name for tool_call in self.tool_calls]

    def format_for_validation(self) -> str:
        """Format the response for human-readable validation output."""
        parts: list[str] = []
        for message in self.messages:
            if message.type == "human":
                parts.append(f"Human: {message.content}")
            elif message.type == "ai":
                if message.tool_calls:
                    parts.append("AI Tool Calls:")
                    for tool_call in message.tool_calls:
                        parts.append(f"  - {tool_call.name}: {tool_call.args}")
                if message.content:
                    parts.append(f"AI Response: {message.content}")
            elif message.type == "tool":
                tool_name = message.tool_name or "unknown"
                parts.append(f"Tool Response ({tool_name}): {message.content}")
        return "\n\n".join(parts)


__all__ = ["ToolCall", "Message", "AgentResponse"]
