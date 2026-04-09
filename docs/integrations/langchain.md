# LangChain / LangGraph integration

Use this guide when you already have a LangChain or LangGraph-style agent and want Goose around it without rewriting
your whole app around a different agent contract.

If you are starting from zero, or you do not need LangChain-specific adapters yet, use the framework-agnostic guide:
[`../getting-started.md`](../getting-started.md).

## What stays the same

Even on the LangChain path, Goose still expects the same scaffold and the same test authoring model:

```bash
goose init
```

```text
gooseapp/
├── README.md
├── __init__.py
├── app.py
├── conftest.py
└── tests/
    ├── __init__.py
    └── test_example.py
```

The parts that do **not** change:

- tests still use `goose.case(...)`
- fixtures still live in `gooseapp/conftest.py`
- fixture injection still matches by **test parameter name**
- `gooseapp/app.py` still owns tools, chat agents, and reload settings

The main difference is your `query(...)` function: instead of building `AgentResponse` manually, you usually adapt a
LangChain payload into `AgentResponse.from_langchain(...)`.

## 1. Install and scaffold

Required for the first test run:

```bash
pip install llm-goose
```

Optional for the browser UI:

```bash
npm install -g @llm-goose/dashboard-cli
```

Then scaffold the local Goose workspace:

```bash
goose init
```

## 2. Create a LangChain-backed `query(...) -> AgentResponse`

Minimal adapter:

```python
from goose.testing.models.messages import AgentResponse


def query(message: str) -> AgentResponse:
    raw_response = my_langchain_agent.invoke(
        {
            "messages": [
                {"role": "user", "content": message},
            ]
        }
    )
    return AgentResponse.from_langchain(raw_response)
```

That is the key LangChain delta:

- Goose still passes the exact `query=` string from `goose.case(...)`
- your adapter still returns `AgentResponse`
- the easiest bridge is `AgentResponse.from_langchain(...)`

If your LangChain app wraps the agent call in another service function, put the adapter there. `gooseapp/conftest.py`
only needs to import the final `query(...)` entrypoint.

## 3. Register the Goose fixture

```python
from goose.testing import Goose, fixture
from my_agent.query_adapter import query


@fixture()
def goose() -> Goose:
    return Goose(
        agent_query_func=query,
        validator_model="gpt-4o-mini",
    )
```

Exact injection rule:

- Goose injects fixtures by **test parameter name**
- if you use `@fixture()`, the fixture name defaults to the Python function name
- if you use `@fixture(name="goose")`, Goose injects that fixture into `def test_x(goose: Goose)`

You can also register multiple Goose fixtures for different LangChain agents or environments:

```python
@fixture(name="support_goose")
def support_goose_fixture() -> Goose:
    return Goose(agent_query_func=query_support_agent)


@fixture(name="staging_goose")
def staging_goose_fixture() -> Goose:
    return Goose(agent_query_func=query_staging_agent)
```

## 4. Write the first Goose case

```python
from goose.testing import Goose
from my_agent.tools import get_weather


def test_weather_lookup(goose: Goose) -> None:
    goose.case(
        query="What is the weather in San Francisco?",
        expectations=[
            "Agent provides weather information for San Francisco",
            "Response includes the current conditions",
        ],
        expected_tool_calls=[get_weather],
    )
```

That test works exactly like the framework-agnostic version. The only LangChain-specific part is the adapter behind
`agent_query_func=query`.

## 5. Expose the agent in Goose live chat

If you want in-app chat in the dashboard, register the agent in `gooseapp/app.py`:

```python
from goose import GooseApp
from langchain.agents import create_agent
from langchain_core.tools import tool


@tool
def get_weather(city: str) -> str:
    return f"It is sunny in {city}."


agent = create_agent(
    model="gpt-4o-mini",
    tools=[get_weather],
    system_prompt="You are a helpful weather assistant.",
)
agent.name = "Weather Agent"

app = GooseApp(
    agents=[agent],
    tools=[get_weather],
    reload_targets=["my_agent"],
)
```

Important details:

- `agent.name` is required and must be unique
- `GooseApp(agents=[...])` accepts LangChain-compatible agents for live chat
- Goose uses the agent's `astream(...)` path for this integration mode
- if you want the Tooling view too, separately register `tools=[...]` or `tool_groups={...}`

If you only care about tests at first, you can postpone `agents=[...]` until later.

## 6. Hot reload for LangChain apps

Use `reload_targets` for the packages you edit frequently and `reload_exclude` for modules that should stay stable:

```python
app = GooseApp(
    agents=[agent],
    tools=[get_weather],
    reload_targets=["my_agent", "shared_utils"],
    reload_exclude=["my_agent.models"],
)
```

Goose always includes `gooseapp` automatically. Before test discovery and execution it reloads source modules, then
re-imports `gooseapp.conftest`.

See [`../running-goose.md`](../running-goose.md) for the full runtime model.

## 7. Run the loop

```bash
goose test list gooseapp.tests
goose test run -v gooseapp.tests
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

## Where to go next

- Want the framework-agnostic base mental model? [`../getting-started.md`](../getting-started.md)
- Need the test reference? [`../testing.md`](../testing.md)
- Need runtime and reload details? [`../running-goose.md`](../running-goose.md)
- Want the dashboard tour? [`../dashboard.md`](../dashboard.md)

If you later want finer control over streamed chat events, move from the LangChain adapter path to a Goose-native chat
agent that implements `astream_goose(...)`.
