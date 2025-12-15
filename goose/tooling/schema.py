"""Schema extraction for LangChain tools."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

from pydantic import BaseModel


class ToolParameter(BaseModel):
    """A single parameter for a tool."""

    name: str
    type: str
    description: str | None = None
    required: bool = True
    default: Any | None = None


class ToolSchema(BaseModel):
    """Schema for a LangChain tool."""

    name: str
    description: str
    group: str | None = None
    parameters: list[ToolParameter]
    json_schema: dict[str, Any] | None = None


def _extract_tool_group(tool: Callable[..., Any], goose_app: Any | None = None) -> str | None:
    # First check GooseApp's tool_groups
    if goose_app is not None:
        tool_name = getattr(tool, "name", None) or getattr(tool, "__name__", None)
        if tool_name and hasattr(goose_app, "get_tool_group"):
            group = goose_app.get_tool_group(tool_name)
            if group:
                return group

    # Fallback to tool's own group attribute
    group = getattr(tool, "group", None)
    if isinstance(group, str) and group.strip():
        return group.strip()

    return None


def extract_tool_schema(tool: Callable, goose_app: Any | None = None) -> ToolSchema:
    """Extract schema information from a LangChain tool.

    Args:
        tool: A LangChain @tool decorated function or StructuredTool.
        goose_app: Optional GooseApp instance for tool group lookup.

    Returns:
        ToolSchema with name, description, and parameters.
    """
    # Get tool name
    if hasattr(tool, "name"):
        name = tool.name
    elif hasattr(tool, "__name__"):
        name = tool.__name__
    else:
        name = type(tool).__name__

    # Get description
    description = getattr(tool, "description", None)
    if description is None:
        description = getattr(tool, "__doc__", None) or "No description available"

    # Get parameters from args_schema (Pydantic model)
    parameters: list[ToolParameter] = []
    json_schema: dict[str, Any] | None = None

    if hasattr(tool, "args_schema") and tool.args_schema is not None:
        args_schema = tool.args_schema

        # Get JSON schema from Pydantic model
        if hasattr(args_schema, "model_json_schema"):
            json_schema = args_schema.model_json_schema()
        elif hasattr(args_schema, "schema"):
            json_schema = args_schema.schema()

        # Extract parameters from Pydantic model fields
        if hasattr(args_schema, "model_fields"):
            for field_name, field_info in args_schema.model_fields.items():
                param_type = "string"  # Default

                # Try to get the type annotation
                if field_info.annotation is not None:
                    param_type = _get_type_name(field_info.annotation)

                # Get description from field
                param_description = None
                if hasattr(field_info, "description"):
                    param_description = field_info.description

                # Check if required
                required = field_info.is_required()

                # Get default value
                default = None
                if not required and field_info.default is not None:
                    default = field_info.default

                parameters.append(
                    ToolParameter(
                        name=field_name,
                        type=param_type,
                        description=param_description,
                        required=required,
                        default=default,
                    )
                )

    return ToolSchema(
        name=name,
        description=description,
        group=_extract_tool_group(tool, goose_app),
        parameters=parameters,
        json_schema=json_schema,
    )


# Type mapping for basic Python types to JSON Schema type names
_TYPE_NAME_MAP: dict[type, str] = {
    str: "string",
    int: "integer",
    float: "number",
    bool: "boolean",
}


def _get_type_name(annotation: Any) -> str:
    """Get a human-readable type name from a type annotation."""
    if annotation is None:
        return "any"

    # Handle basic types via lookup
    if annotation in _TYPE_NAME_MAP:
        return _TYPE_NAME_MAP[annotation]

    # Handle typing constructs
    origin = getattr(annotation, "__origin__", None)
    if origin is not None:
        args = getattr(annotation, "__args__", ())
        if origin is list:
            return f"array[{_get_type_name(args[0])}]" if args else "array"
        if origin is dict:
            return "object"

    # Fall back to string representation
    if hasattr(annotation, "__name__"):
        return annotation.__name__.lower()

    return str(annotation)


def list_tool_schemas(tools: Sequence[Callable[..., Any]], goose_app: Any | None = None) -> list[ToolSchema]:
    """Extract schemas from a list of tools.

    Args:
        tools: List of LangChain @tool decorated functions.
        goose_app: Optional GooseApp instance for tool group lookup.

    Returns:
        List of ToolSchema objects.
    """
    return [extract_tool_schema(tool, goose_app) for tool in tools]


def get_tool_by_name(tools: Sequence[Callable[..., Any]], name: str) -> Callable[..., Any] | None:
    """Find a tool by name from a list of tools.

    Args:
        tools: List of LangChain @tool decorated functions.
        name: Name of the tool to find.

    Returns:
        The tool if found, None otherwise.
    """
    for tool in tools:
        if hasattr(tool, "name"):
            tool_name = tool.name
        elif hasattr(tool, "__name__"):
            tool_name = tool.__name__
        else:
            tool_name = type(tool).__name__

        if tool_name == name:
            return tool
    return None


__all__ = [
    "ToolParameter",
    "ToolSchema",
    "extract_tool_schema",
    "list_tool_schemas",
    "get_tool_by_name",
]
