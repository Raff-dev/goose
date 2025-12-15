"""Pydantic models for tooling API."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from goose.tooling.schema import ToolParameter


class ToolSummary(BaseModel):
    """Summary of a tool for listing."""

    name: str
    description: str
    group: str | None = None
    parameter_count: int


class ToolDetail(BaseModel):
    """Detailed information about a tool."""

    name: str
    description: str
    group: str | None = None
    parameters: list[ToolParameter]
    json_schema: dict[str, Any] | None = None


class InvokeRequest(BaseModel):
    """Request to invoke a tool."""

    args: dict[str, Any] = {}


class InvokeResponse(BaseModel):
    """Response from a tool invocation."""

    success: bool
    result: Any | None = None
    error: str | None = None


__all__ = [
    "ToolSummary",
    "ToolDetail",
    "InvokeRequest",
    "InvokeResponse",
]
