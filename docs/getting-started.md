# Getting started

This is the **canonical first-run path** for Goose.

Start here when you want Goose's native scaffold and chat contract. The entrypoint is **`goose init`**. If you
already have a LangChain or LangGraph agent, keep this page as context and use the optional
[`LangChain integration guide`](integrations/langchain.md) for the adapter path.

## 1. Install

```bash
pip install llm-goose
npm install -g @llm-goose/dashboard-cli
```

## 2. Run `goose init`

```bash
goose init
```

That creates the fixed `gooseapp/` layout Goose expects:

```text
gooseapp/
├── app.py
├── conftest.py
└── tests/
    └── test_example.py
```

For the full scaffold contract, overwrite behavior, and file-by-file breakdown, see
[`goose-init.md`](goose-init.md).

## 3. Edit `gooseapp/app.py` first

`gooseapp/app.py` is where you tell Goose what exists in your app:

- `agents=[...]` for live chat
- `tools=[...]` or `tool_groups={...}` for the Tooling view
- `reload_targets=[...]` for packages you want reloaded during development
- `reload_exclude=[...]` for modules that should stay stable

Minimal Goose-native example:

```python
from goose import GooseApp
from goose.chatting.agent_protocol import GooseAgentEvent


class EchoAgent:
    name = "Echo Agent"

    async def astream_goose(self, *, conversation, messages):
        content = messages[-1].content if messages else ""
        yield GooseAgentEvent(type="token", data={"content": f"Echo: {content}"})
        yield GooseAgentEvent(type="message_end")


app = GooseApp(
    agents=[EchoAgent()],
    reload_targets=["my_agent_package"],
)
```

You do not need to solve every config option on day one. For a first run, it is enough to register one agent and the
packages you expect to edit often.

## 4. Edit `gooseapp/conftest.py` next

`gooseapp/conftest.py` wires your tests to the real agent entrypoint.

What to change first:

- import your real `query(...)` function
- return a configured `Goose(...)` fixture
- add lifecycle hooks only if your app needs setup/teardown

Typical starting point:

```python
from goose.testing import Goose, fixture
from my_agent import query


@fixture(name="goose")
def goose_fixture() -> Goose:
    return Goose(
        agent_query_func=query,
        validator_model="gpt-4o-mini",
    )
```

If your tests need database resets or other setup around each case, extend this file with hooks as shown in
[`testing.md`](testing.md).

## 5. Run the first Goose loop

```bash
goose test list
goose test run -v gooseapp.tests
goose api
goose-dashboard
```

What each command gives you:

- `goose test list` - confirm Goose discovers your cases
- `goose test run -v gooseapp.tests` - run them with transcript and tool activity in the terminal
- `goose api` - start the Python backend on `127.0.0.1:8730`
- `goose-dashboard` - open the UI on `http://localhost:8729`

From there:

- use the **Testing** view to rerun cases and inspect traces
- use the **Tooling** view to debug one tool in isolation
- use the **Chat** view to replay a live flow before turning it into a test

See [`running-goose.md`](running-goose.md) for runtime details and [`dashboard.md`](dashboard.md) for the UI workflow.

## 6. Where to branch out

- Need deeper scaffold guidance? [`goose-init.md`](goose-init.md)
- Ready to write better cases? [`testing.md`](testing.md)
- Need the runtime model and ports? [`running-goose.md`](running-goose.md)
- Want the dashboard tour? [`dashboard.md`](dashboard.md)
- Already on LangChain or LangGraph? [`integrations/langchain.md`](integrations/langchain.md)
