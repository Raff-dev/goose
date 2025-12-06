"""Tool executor for invoking LangChain tools."""

from __future__ import annotations

import asyncio
import inspect
from collections.abc import Callable
from typing import Any


class ToolExecutionError(Exception):
    """Error raised when tool execution fails."""

    def __init__(self, message: str, tool_name: str, cause: Exception | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.tool_name = tool_name
        self.cause = cause


def is_langchain_tool(func: Callable) -> bool:
    """Check if a function is a LangChain @tool decorated function.

    LangChain tools have specific attributes set by the @tool decorator.
    """
    # LangChain StructuredTool or Tool instances
    if hasattr(func, "name") and hasattr(func, "description") and hasattr(func, "invoke"):
        return True

    # Also check for the @tool decorator which sets these attributes
    if hasattr(func, "name") and hasattr(func, "args_schema"):
        return True

    return False


def get_tool_name(func: Callable) -> str:
    """Get the name of a LangChain tool."""
    if hasattr(func, "name"):
        return func.name
    return func.__name__


def invoke_tool(tool: Callable, args: dict[str, Any]) -> Any:
    """Invoke a LangChain tool with the given arguments.

    Handles both sync and async tools. For async tools, runs them
    in an event loop.

    Args:
        tool: A LangChain @tool decorated function or StructuredTool.
        args: Dictionary of arguments to pass to the tool.

    Returns:
        The result from the tool invocation.

    Raises:
        ToolExecutionError: If the tool execution fails.
    """
    tool_name = get_tool_name(tool)

    try:
        # LangChain tools have an invoke method
        if hasattr(tool, "invoke"):
            result = tool.invoke(args)

            # Handle async results
            if asyncio.iscoroutine(result):
                loop = asyncio.new_event_loop()
                try:
                    result = loop.run_until_complete(result)
                finally:
                    loop.close()

            return result

        # Direct function call for plain functions (shouldn't happen with @tool)
        if inspect.iscoroutinefunction(tool):
            loop = asyncio.new_event_loop()
            try:
                result = loop.run_until_complete(tool(**args))
            finally:
                loop.close()
            return result

        return tool(**args)

    except Exception as exc:
        raise ToolExecutionError(
            message=str(exc),
            tool_name=tool_name,
            cause=exc,
        ) from exc


async def invoke_tool_async(tool: Callable, args: dict[str, Any]) -> Any:
    """Invoke a LangChain tool asynchronously.

    Args:
        tool: A LangChain @tool decorated function or StructuredTool.
        args: Dictionary of arguments to pass to the tool.

    Returns:
        The result from the tool invocation.

    Raises:
        ToolExecutionError: If the tool execution fails.
    """
    tool_name = get_tool_name(tool)

    try:
        # LangChain tools have an ainvoke method for async
        if hasattr(tool, "ainvoke"):
            return await tool.ainvoke(args)

        # Fall back to invoke in a thread pool
        if hasattr(tool, "invoke"):
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, tool.invoke, args)

        # Direct function call
        if inspect.iscoroutinefunction(tool):
            return await tool(**args)

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: tool(**args))

    except Exception as exc:
        raise ToolExecutionError(
            message=str(exc),
            tool_name=tool_name,
            cause=exc,
        ) from exc


__all__ = [
    "ToolExecutionError",
    "is_langchain_tool",
    "get_tool_name",
    "invoke_tool",
    "invoke_tool_async",
]
