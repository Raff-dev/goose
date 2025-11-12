"""Compatibility shim: message models were moved to `goose.models`.

This module preserves the old import path (`goose.utils`) by re-exporting
the main classes from `goose.models`. Prefer importing from
`goose.models` going forward.
"""

from goose.models import AgentResponse, Message, ToolCall

__all__ = ["ToolCall", "Message", "AgentResponse"]
