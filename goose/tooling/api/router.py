"""Tooling API routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status  # type: ignore[import-not-found]

from goose.api.config import GooseConfig
from goose.tooling.api.schema import InvokeRequest, InvokeResponse, ToolDetail, ToolSummary
from goose.tooling.executor import ToolExecutionError, invoke_tool
from goose.tooling.schema import extract_tool_schema, get_tool_by_name

router = APIRouter()


def _get_tools() -> list:
    """Get the list of tools from the GooseApp."""
    config = GooseConfig()
    if config.goose_app is None:
        return []
    return config.goose_app.tools


@router.get("/tools", response_model=list[ToolSummary])
def list_tools() -> list[ToolSummary]:
    """List all registered tools with their names and descriptions."""
    tools = _get_tools()
    summaries = []

    for tool in tools:
        schema = extract_tool_schema(tool)
        summaries.append(
            ToolSummary(
                name=schema.name,
                description=schema.description,
                parameter_count=len(schema.parameters),
            )
        )

    return summaries


@router.get("/tools/{name}", response_model=ToolDetail)
def get_tool(name: str) -> ToolDetail:
    """Get detailed information about a specific tool."""
    tools = _get_tools()
    tool = get_tool_by_name(tools, name)

    if tool is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool '{name}' not found",
        )

    schema = extract_tool_schema(tool)
    return ToolDetail(
        name=schema.name,
        description=schema.description,
        parameters=schema.parameters,
        json_schema=schema.json_schema,
    )


@router.post("/tools/{name}/invoke", response_model=InvokeResponse)
def invoke_tool_endpoint(name: str, request: InvokeRequest) -> InvokeResponse:
    """Invoke a tool with the given arguments."""
    tools = _get_tools()
    tool = get_tool_by_name(tools, name)

    if tool is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool '{name}' not found",
        )

    try:
        result = invoke_tool(tool, request.args)
        return InvokeResponse(success=True, result=result)
    except ToolExecutionError as exc:
        return InvokeResponse(success=False, error=exc.message)
    except Exception as exc:  # noqa: BLE001
        return InvokeResponse(success=False, error=str(exc))


__all__ = ["router"]
