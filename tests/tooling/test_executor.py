"""Tests for tool executor."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest

from goose.tooling.executor import (
    ToolExecutionError,
    get_tool_name,
    invoke_tool,
    is_langchain_tool,
)


# Create a simple mock tool that mimics LangChain's @tool
class MockTool:
    """Mock LangChain tool for testing."""

    def __init__(self, name: str, func: Callable[..., Any]):
        self.name = name
        self.description = f"Mock tool: {name}"
        self._func = func

    def invoke(self, args: dict[str, Any]) -> Any:
        return self._func(**args)

    def __call__(self, **kwargs: Any) -> Any:
        return self.invoke(kwargs)


class TestIsLangchainTool:
    """Tests for is_langchain_tool function."""

    def test_plain_function_not_tool(self) -> None:
        """Plain functions are not LangChain tools."""

        def plain_func():
            return "hello"

        assert is_langchain_tool(plain_func) is False

    def test_mock_tool_is_tool(self) -> None:
        """Mock tool with name, description, invoke is recognized."""
        tool = MockTool("test_tool", lambda: "result")
        assert is_langchain_tool(tool) is True


class TestGetToolName:
    """Tests for get_tool_name function."""

    def test_gets_name_attribute(self) -> None:
        """Gets name from name attribute."""
        tool = MockTool("my_tool", lambda: None)
        assert get_tool_name(tool) == "my_tool"

    def test_falls_back_to_dunder_name(self) -> None:
        """Falls back to __name__ for plain functions."""

        def my_function():
            pass

        assert get_tool_name(my_function) == "my_function"


class TestInvokeTool:
    """Tests for invoke_tool function."""

    def test_invoke_with_args(self) -> None:
        """Invokes tool with arguments."""

        def add(a: int, b: int) -> int:
            return a + b

        tool = MockTool("add", add)
        result = invoke_tool(tool, {"a": 2, "b": 3})
        assert result == 5

    def test_invoke_with_no_args(self) -> None:
        """Invokes tool with no arguments."""

        def greet() -> str:
            return "hello"

        tool = MockTool("greet", greet)
        result = invoke_tool(tool, {})
        assert result == "hello"

    def test_invoke_raises_execution_error(self) -> None:
        """Raises ToolExecutionError on failure."""

        def fail():
            raise ValueError("intentional error")

        tool = MockTool("fail", fail)

        with pytest.raises(ToolExecutionError) as exc_info:
            invoke_tool(tool, {})

        assert "intentional error" in exc_info.value.message
        assert exc_info.value.tool_name == "fail"

    def test_invoke_plain_function(self) -> None:
        """Can invoke plain function directly."""

        def multiply(x: int, y: int) -> int:
            return x * y

        # Plain function without invoke method
        result = invoke_tool(multiply, {"x": 3, "y": 4})
        assert result == 12
