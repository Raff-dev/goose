# Copilot Instructions for Goose Outfitters Project

## Development Environment

-   Always use `uv` to run Python code and manage dependencies
-   Use `uv run` for executing scripts and commands
-   Use `uv add` for adding dependencies

## Code Style

-   Always use absolute imports (e.g., `from goose.agent import query`)
-   Never use relative imports (e.g., `from .agent import query`)
-   Never use dynamic imports (e.g., `importlib.import_module()`)
-   Always use `from __future__ import annotations` at the top of files with type annotations
-   Never use quoted forward references (e.g., `"AgentResponse"` - just use `AgentResponse`)
-   Always use 120 character line length maximum
-   Follow PEP 8 style guidelines

## Project Structure

-   Keep tools in `goose/tools.py`
-   Keep agent logic in `goose/agent.py`
-   Keep data models in `goose/models.py`
-   Keep data instances in `goose/data.py`
-   Keep CLI entrypoints in `goose/entrypoints.py`
-   Keep examples in `examples/` directory

## LangChain Usage

-   Use the simple `create_agent()` pattern with tools and system prompt
-   Prefer OpenAI GPT-4o-mini for cost-effective development
-   Handle conversation history properly with message conversion
-   Use `@tool` decorators for all tool functions
-   Provide comprehensive docstrings with Args/Returns sections

## Testing

-   Test imports with `uv run python -c "from goose.module import function"`
-   Test CLI commands with `uv run command --help`
-   Validate agent responses with sample questions
-   Check for lint errors after changes

## File Organization

-   Use Pydantic models for all data structures
-   Keep static data in `goose/data.py` as instantiated model objects
-   Export tools list from `goose/tools.py` as `TOOLS`
-   Use proper error handling and JSON serialization for tool responses
