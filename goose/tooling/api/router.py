"""Tooling API routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status  # type: ignore[import-not-found]

from goose.core.config import GooseConfig
from goose.core.reload import reload_source_modules
from goose.tooling.api.schema import InvokeRequest, InvokeResponse, ToolDetail, ToolSummary
from goose.tooling.executor import ToolExecutionError, invoke_tool_async
from goose.tooling.schema import extract_tool_schema, get_tool_by_name

router = APIRouter()


def _get_tools() -> list:
    """Get the list of tools from the GooseApp."""
    config = GooseConfig()
    if config.goose_app is None:
        return []
    return config.goose_app.tools


def _reload_tools() -> list:
    """Reload tool modules and return fresh tools from GooseApp."""
    config = GooseConfig()
    # Exclude conftest modules - tooling doesn't need fixtures
    reload_source_modules(extra_exclude_suffixes=[".conftest"])
    config.refresh_app()
    return _get_tools()


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
async def invoke_tool_endpoint(name: str, request: InvokeRequest) -> InvokeResponse:
    """Invoke a tool with the given arguments.

    Reloads tool modules before invocation to pick up code changes.
    """
    tools = _reload_tools()
    tool = get_tool_by_name(tools, name)

    if tool is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool '{name}' not found",
        )

    try:
        result = await invoke_tool_async(tool, request.args)
        return InvokeResponse(success=True, result=result)
    except ToolExecutionError as exc:
        return InvokeResponse(success=False, error=exc.message)
    except Exception as exc:  # noqa: BLE001 pylint: disable=broad-exception-caught
        # Intentionally catch all exceptions from user tools to return clean error
        return InvokeResponse(success=False, error=str(exc))


__all__ = ["router"]
