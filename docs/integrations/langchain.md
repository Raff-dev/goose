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

If you are starting from zero, the usual Goose-native flow is:

1. [`goose-init.md`](../goose-init.md)
2. [`testing.md`](../testing.md)
3. [`running-goose.md`](../running-goose.md)
4. [`dashboard.md`](../dashboard.md)

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
- If you also want Tooling view support, separately register tools in `GooseApp(tools=[...])` or `tool_groups={...}`.

## When this path is the right fit

Choose this integration when:

- you already have a working LangChain or LangGraph agent
- you want Goose's dashboard and traces without rebuilding your agent contract first
- live chat is the first thing you want to unlock

Do **not** choose it just because you want tests. Goose test authoring still happens through `gooseapp/conftest.py`,
fixtures, and `goose.case(...)` either way.

## Minimal scaffold shape

Even on the LangChain path, Goose still expects the same scaffold:

```text
gooseapp/
├── app.py
├── conftest.py
└── tests/
```

- `gooseapp/app.py` is where you expose the LangChain agent to Goose via `GooseApp(agents=[agent])`
- `gooseapp/conftest.py` is where you wire your test fixture to the agent's query function
- `gooseapp/tests/` is where your Goose cases live

See [`goose-init.md`](../goose-init.md) for the generated scaffold in detail.

## Running it

```bash
goose api
goose-dashboard
```

By default:

- `goose api` serves the backend on `127.0.0.1:8730`
- `goose-dashboard` serves the UI on `http://localhost:8729`

If your API is elsewhere:

```bash
goose-dashboard --api-url http://localhost:9000
GOOSE_API_URL=http://localhost:9000 goose-dashboard
```

See [`running-goose.md`](../running-goose.md) for the full runtime loop.

## Testing a LangChain-backed app

LangChain support gets your agent into Goose chat, but your tests should still follow the normal Goose patterns:

- create a Goose fixture in `gooseapp/conftest.py`
- send queries with `goose.case(...)`
- use `expected_tool_calls=[...]` when tool routing matters
- inspect failures in the dashboard Testing view

See:

- [`testing.md`](../testing.md)
- [`dashboard.md`](../dashboard.md)

If you later want a framework-agnostic contract or more control over streamed events, move to the Goose-native path in [`docs/getting-started.md`](../getting-started.md).
