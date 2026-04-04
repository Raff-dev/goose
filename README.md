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

## What Goose is

Goose is a **Python library, CLI, and web dashboard for LLM agents**. Think of it like **pytest for agent
workflows**: you scaffold a `gooseapp/`, register your agent and tools, write `goose.case(...)` tests in Python,
then debug failures in the dashboard.

Goose is **Goose-native first**: the default path is `goose init` plus a Goose-native agent contract. If you already
have LangChain or LangGraph in place, that path stays available as an optional integration.

## What it looks like

![Goose dashboard overview](images/dashboard_view.png)

![Goose testing detail](images/dashboard_testing_detail.png)

## Why Goose?

- **Natural-language expectations** – Describe the behavior you want and let Goose validate it.
- **Tool call assertions** – Check what your agent actually did, not just what it said.
- **Full execution traces** – Inspect messages, tool calls, tool outputs, and validation results.
- **Live chat for iteration** – Try agents in the dashboard while you develop.
- **Hot reload** – Re-run against updated code without restarting the app.

## Core workflow

1. **Scaffold the app** with `goose init`
2. **Edit `gooseapp/app.py`** to register agents, tools, and reload targets
3. **Edit `gooseapp/conftest.py`** to wire the `goose` fixture to your real query function
4. **Write cases in `gooseapp/tests/`** with `goose.case(...)`
5. **Run the loop** with `goose test run`, `goose api`, and `goose-dashboard`

## Install

```bash
pip install llm-goose
npm install -g @llm-goose/dashboard-cli
```

## `goose init` creates the path

```bash
goose init
```

```text
gooseapp/
├── app.py
├── conftest.py
└── tests/
    └── test_example.py
```

- `app.py` configures the Goose surface area
- `conftest.py` wires your test fixture
- `tests/` holds the cases you run from CLI or dashboard

See [`docs/goose-init.md`](docs/goose-init.md) for the full scaffold contract.

## A real Goose case

```python
from example_system.models import Product
from example_system.tools import get_product_details
from goose.testing import Goose


def test_price_lookup_hiking_boots(goose: Goose) -> None:
    hiking_boots = Product.objects.get(name="Hiking Boots")
    goose.case(
        query="What's the price of Hiking Boots?",
        expectations=[
            f"Agent provided the correct price (${hiking_boots.price_usd:.2f})",
            "Agent identified the product correctly as 'Hiking Boots'",
        ],
        expected_tool_calls=[get_product_details],
    )
```

That is the core Goose idea: a natural-language case, optional tool assertions, and a trace you can inspect when it
fails.

## Key commands

```bash
goose init                  # scaffold gooseapp/
goose test run gooseapp.tests
goose api
goose-dashboard
```

## Where to go next

- **Canonical first run**: [`docs/getting-started.md`](docs/getting-started.md)
- **Scaffold details**: [`docs/goose-init.md`](docs/goose-init.md)
- **Writing tests**: [`docs/testing.md`](docs/testing.md)
- **Running the API and CLI loop**: [`docs/running-goose.md`](docs/running-goose.md)
- **Using the dashboard**: [`docs/dashboard.md`](docs/dashboard.md)
- **Optional LangChain path**: [`docs/integrations/langchain.md`](docs/integrations/langchain.md)

## License

MIT License – see `LICENSE` for full text.
