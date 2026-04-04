<h1 align="center">LLM Goose 🪿</h1>

<p align="center">
  <strong>LLM-powered testing, traces, and live chat for agent workflows</strong>
</p>

<p align="center">
  <a href="https://pypi.org/project/llm-goose/"><img src="https://img.shields.io/pypi/v/llm-goose.svg?logo=pypi&label=PyPI" alt="PyPI"></a>
  <a href="https://www.npmjs.com/package/@llm-goose/dashboard-cli"><img src="https://img.shields.io/npm/v/@llm-goose/dashboard-cli.svg?logo=npm&label=npm" alt="npm"></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/python-3.13%2B-3776AB?logo=python&logoColor=white" alt="Python"></a>
  <a href="https://github.com/Raff-dev/goose/actions/workflows/ci.yml"><img src="https://github.com/Raff-dev/goose/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="https://github.com/Raff-dev/goose/actions/workflows/ci.yml"><img src="https://img.shields.io/badge/coverage-74%25-brightgreen?logo=codecov&logoColor=white" alt="Coverage"></a>
  <a href="https://github.com/pre-commit/pre-commit"><img src="https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white" alt="pre-commit"></a>
</p>

---

<p align="center">
  Goose is a <strong>Python library, CLI, and web dashboard</strong> for testing and debugging LLM agents.<br>
  Start with Goose-native chat agents, inspect traces in the dashboard, and keep LangChain integration available when you already have it.
</p>

<p align="center">
  <a href="https://raff-dev.github.io/goose"><strong>Visit the landing page</strong></a>
</p>

## Why Goose?

- **Natural-language expectations** – Describe the outcome you want and let Goose validate it.
- **Tool call assertions** – Check what your agent actually did, not just what it said.
- **Full execution traces** – Inspect messages, tool calls, tool outputs, and validation results.
- **Live chat for iteration** – Try agents in the dashboard while you develop.
- **Hot reload** – Re-run against updated code without restarting the app.

## Goose at a glance

| You want to… | Use Goose for… |
| --- | --- |
| Test agent behavior | Plain-English expectations plus optional tool assertions |
| Debug a live workflow | Dashboard traces, chat history, and tool visibility |
| Build a new chat path | Goose-native agents with `astream_goose(...)` |
| Bring an existing agent | LangChain-compatible integration via `astream(...)` |

## Install

```bash
pip install llm-goose
npm install -g @llm-goose/dashboard-cli
```

## Start here

- **New project / default path**: [`docs/getting-started.md`](docs/getting-started.md)
- **Existing LangChain or LangGraph agent**: [`docs/integrations/langchain.md`](docs/integrations/langchain.md)
- **Initialize a scaffold**: `goose init`

## Minimal GooseApp

```python
from goose import GooseApp
from goose.chatting.agent_protocol import GooseAgentEvent


class EchoAgent:
    name = "Echo Agent"

    async def astream_goose(self, *, conversation, messages):
        content = messages[-1].content if messages else ""
        yield GooseAgentEvent(type="token", data={"content": f"Echo: {content}"})
        yield GooseAgentEvent(type="message_end")


app = GooseApp(agents=[EchoAgent()])
```

For the full onboarding flow, see [`docs/getting-started.md`](docs/getting-started.md).

## CLI and dashboard

```bash
# Initialize a gooseapp/ project structure
goose init

# Run tests
goose test run gooseapp.tests

# Start the API
goose api

# Open the dashboard
goose-dashboard
```

## License

MIT License – see `LICENSE` for full text.
