"""Pydantic models for structured agent responses and tool calls."""

from __future__ import annotations

from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from pydantic import BaseModel, Field


class TokenUsage(BaseModel):
    """Token usage statistics for an LLM interaction."""

    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0


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
    tool_call_id: str | None = None
    token_usage: TokenUsage | None = None

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
                token_usage = _extract_token_usage(message)
                return cls(type="ai", content=content, tool_calls=tool_calls, token_usage=token_usage)
            case "tool":
                content = str(getattr(message, "content", ""))
                tool_name = getattr(message, "name", "unknown")
                tool_call_id = getattr(message, "tool_call_id", None)
                return cls(type="tool", content=content, tool_name=tool_name, tool_call_id=tool_call_id)
            case _:
                return cls(type=msg_type, content=str(message))

    def to_langchain(self) -> Any:
        """Convert this Message to a LangChain message object."""
        match self.type:
            case "human":
                return HumanMessage(content=self.content)
            case "ai":
                tool_calls = [{"name": tc.name, "args": tc.args, "id": tc.id or ""} for tc in self.tool_calls]
                return AIMessage(content=self.content, tool_calls=tool_calls)
            case "tool":
                return ToolMessage(
                    content=self.content, name=self.tool_name or "", tool_call_id=self.tool_call_id or ""
                )
            case _:
                return HumanMessage(content=self.content)


def _extract_token_usage(message: Any) -> TokenUsage | None:
    """Extract token usage from a LangChain AI message's response metadata."""
    response_metadata = getattr(message, "response_metadata", None)
    if not response_metadata:
        return None

    # OpenAI format
    usage = response_metadata.get("token_usage") or response_metadata.get("usage")
    if not usage:
        return None

    return TokenUsage(
        input_tokens=usage.get("prompt_tokens", 0) or usage.get("input_tokens", 0),
        output_tokens=usage.get("completion_tokens", 0) or usage.get("output_tokens", 0),
        total_tokens=usage.get("total_tokens", 0),
    )


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
    def token_usage(self) -> TokenUsage:
        """Return aggregated token usage across all messages."""
        total = TokenUsage()
        for message in self.messages:
            if message.token_usage:
                total.input_tokens += message.token_usage.input_tokens
                total.output_tokens += message.token_usage.output_tokens
                total.total_tokens += message.token_usage.total_tokens
        return total

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


__all__ = ["ToolCall", "Message", "AgentResponse", "TokenUsage"]
