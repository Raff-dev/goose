# Goose LLM

A comprehensive testing framework for validating Large Language Model (LLM) agent behavior and tool usage patterns.

## Features

- **Agent Behavior Testing**: Validate LLM agent responses against expected patterns
- **Tool Call Validation**: Ensure agents use tools correctly and in the right sequence
- **Flexible Test Patterns**: Support for various tool call validation strategies
- **Pydantic Models**: Type-safe data structures throughout
- **Async Support**: Built-in support for asynchronous operations

## Installation

```bash
pip install goose-llm
```

## Quick Start

```python
import goose

# Create a test case
case = goose.case(
    query="What products do you have?",
    expectations=[
        "Agent should list available products",
        "Agent should use the search_products tool"
    ]
)

# Validate the agent response
result = case.validate(agent_response)
```

## Development

This project uses modern Python packaging with uv for dependency management.

```bash
# Install dependencies
uv sync

# Run tests
uv run pytest

# Build package
uv build

# Start local Postgres for the example system
docker compose -f example_system/docker-compose.yaml up -d

# Apply Django migrations for the example system app
uv run python -m django migrate --settings=example_system.settings
```

## License

MIT License - see LICENSE file for details.
