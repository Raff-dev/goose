# LangChain integration

Use this guide when you already have a LangChain or LangGraph-style agent and want to plug it into Goose without rewriting your app around the Goose-native protocol.

If you are starting greenfield, prefer [`docs/getting-started.md`](../getting-started.md). That path is simpler and gives you direct control over Goose chat events.

## When to use this path

Choose **LangChain integration** when:

- your agent already exposes LangChain-compatible streaming via `astream(...)`
- you want Goose chat and traces around an existing agent
- you are not ready to introduce a Goose-native event layer yet

Choose **Goose-native** when:

- you are building a new chat path
- you want explicit control over tokens, tool events, and conversation metadata
- you want the default Goose docs path

## Minimal example

```python
from goose import GooseApp
from langchain.agents import create_agent
from langchain_core.tools import tool


@tool
def get_weather(city: str) -> str:
    """Return the current weather for a city."""
    return f"It is sunny in {city}."


agent = create_agent(
    model="gpt-4o-mini",
    tools=[get_weather],
    system_prompt="You are a helpful weather assistant.",
)
agent.name = "Weather Agent"

app = GooseApp(agents=[agent])
```

Notes:

- `agent.name` is required. Goose uses it in the UI and requires names to be unique.
- `GooseApp(agents=[...])` accepts LangChain-compatible agents for live chat.
- Goose uses the agent's `astream(...)` path for this integration mode.

## Run it

```bash
goose api
goose-dashboard
```

If you later want a framework-agnostic contract or more control over streamed events, move to the Goose-native path in [`docs/getting-started.md`](../getting-started.md).
