"""Tests for tool schema extraction."""

from __future__ import annotations

from goose.tooling.schema import (
    extract_tool_schema,
    get_tool_by_name,
    list_tool_schemas,
)


# Mock tool with args_schema (like LangChain @tool)
class MockArgsSchema:
    """Mock Pydantic model for tool args."""

    model_fields = {}

    @classmethod
    def model_json_schema(cls):
        return {"type": "object", "properties": {}}


class MockToolWithSchema:
    """Mock LangChain tool with args_schema."""

    def __init__(self, name: str, description: str, args_schema=None):
        self.name = name
        self.description = description
        self.args_schema = args_schema

    def invoke(self, args: dict):
        return args


class TestExtractToolSchema:
    """Tests for extract_tool_schema function."""

    def test_extracts_name_and_description(self) -> None:
        """Extracts name and description from tool."""
        tool = MockToolWithSchema("my_tool", "Does something useful")

        schema = extract_tool_schema(tool)

        assert schema.name == "my_tool"
        assert schema.description == "Does something useful"

    def test_extracts_from_plain_function(self) -> None:
        """Extracts from plain function with docstring."""

        def my_func():
            """This function does things."""

        schema = extract_tool_schema(my_func)

        assert schema.name == "my_func"
        assert "This function does things" in schema.description

    def test_extracts_json_schema(self) -> None:
        """Extracts JSON schema from args_schema."""
        tool = MockToolWithSchema("tool", "desc", args_schema=MockArgsSchema)

        schema = extract_tool_schema(tool)

        assert schema.json_schema is not None
        assert schema.json_schema["type"] == "object"


class TestListToolSchemas:
    """Tests for list_tool_schemas function."""

    def test_lists_multiple_tools(self) -> None:
        """Lists schemas for multiple tools."""
        tools = [
            MockToolWithSchema("tool_a", "Description A"),
            MockToolWithSchema("tool_b", "Description B"),
        ]

        schemas = list_tool_schemas(tools)

        assert len(schemas) == 2
        assert schemas[0].name == "tool_a"
        assert schemas[1].name == "tool_b"

    def test_empty_list(self) -> None:
        """Handles empty tools list."""
        schemas = list_tool_schemas([])
        assert schemas == []


class TestGetToolByName:
    """Tests for get_tool_by_name function."""

    def test_finds_tool_by_name(self) -> None:
        """Finds a tool by its name."""
        tool_a = MockToolWithSchema("tool_a", "A")
        tool_b = MockToolWithSchema("tool_b", "B")
        tools = [tool_a, tool_b]

        result = get_tool_by_name(tools, "tool_b")

        assert result is tool_b

    def test_returns_none_if_not_found(self) -> None:
        """Returns None if tool not found."""
        tools = [MockToolWithSchema("tool_a", "A")]

        result = get_tool_by_name(tools, "nonexistent")

        assert result is None

    def test_finds_plain_function(self) -> None:
        """Finds plain function by __name__."""

        def my_func():
            pass

        tools = [my_func]

        result = get_tool_by_name(tools, "my_func")

        assert result is my_func
