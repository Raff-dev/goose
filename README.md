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
  Scaffold a <code>gooseapp/</code>, point Goose at your real query function, write
  <code>goose.case(...)</code> tests, then expose tools and live chat when you want the full dashboard loop.
</p>

<p align="center">
  <a href="https://raff-dev.github.io/goose"><strong>Visit the landing page</strong></a>
</p>

## What it looks like

![Goose dashboard overview](images/dashboard_view.png)

![Goose testing detail](images/dashboard_testing_detail.png)

## Why Goose?

- **Natural-language expectations** – Describe the behavior you want and let Goose validate it.
- **Tool call assertions** – Check what your agent actually did, not just what it said.
- **Full execution traces** – Inspect messages, tool calls, tool outputs, and validation results.
- **Live chat for iteration** – Try agents in the dashboard while you develop.
- **Hot reload** – Re-run against updated code without restarting the app.

## Choose your path

- **Framework-agnostic quickstart** – integrate Goose into an existing Python app, regardless of framework:
  [`docs/getting-started.md`](docs/getting-started.md)
- **LangChain / LangGraph integration** – keep your existing LangChain-style agent and add Goose around it:
  [`docs/integrations/langchain.md`](docs/integrations/langchain.md)

If you are starting from zero, the framework-agnostic quickstart is the default path.

## Core workflow

1. **Scaffold the app** with `goose init`
2. **Point Goose at `query(...) -> AgentResponse`** in `gooseapp/conftest.py`
3. **Write cases in `gooseapp/tests/`** with `goose.case(...)`
4. **Run the first loop** with `goose test list` and `goose test run`
5. **Expand into tools, chat, and hot reload** through `gooseapp/app.py`

## Install

Required for the first test run:

```bash
pip install llm-goose
```

Optional for the browser UI:

```bash
npm install -g @llm-goose/dashboard-cli
```

## `goose init` creates the path

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

- `app.py` configures tools, live chat agents, and hot reload
- `conftest.py` wires the Goose fixture to your real query function
- `tests/` holds the cases you run from the CLI or dashboard

See [`docs/goose-init.md`](docs/goose-init.md) for the full scaffold contract.

## Minimal first test

```python
from goose.testing import Goose


def test_agent_responds(goose: Goose) -> None:
    goose.case(
        query="Hello, what can you help me with?",
        expectations=[
            "Agent responds with a greeting or acknowledgment",
            "Agent describes its capabilities or offers assistance",
        ],
    )
```

`goose` is injected from the fixture you register in `gooseapp/conftest.py`. The full query -> fixture -> test path is
documented in [`docs/getting-started.md`](docs/getting-started.md).

## Key commands

```bash
goose init                  # scaffold gooseapp/
goose test list gooseapp.tests
goose test run gooseapp.tests
goose api
goose-dashboard
```

## Where to go next

- **Framework-agnostic quickstart**: [`docs/getting-started.md`](docs/getting-started.md)
- **LangChain / LangGraph integration**: [`docs/integrations/langchain.md`](docs/integrations/langchain.md)
- **Scaffold details**: [`docs/goose-init.md`](docs/goose-init.md)
- **Writing tests**: [`docs/testing.md`](docs/testing.md)
- **Running the API and CLI loop**: [`docs/running-goose.md`](docs/running-goose.md)
- **Using the dashboard**: [`docs/dashboard.md`](docs/dashboard.md)

## License

MIT License – see `LICENSE` for full text.
