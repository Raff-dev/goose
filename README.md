# Goose LLM 🪿

Goose is a batteries‑included **Python library and CLI** for validating LLM agents end‑to‑end.

Design conversational test cases, run them locally or in CI, and (optionally) plug in a React dashboard – all while staying in Python.

Turn your “vibes‑based” LLM evaluations into **repeatable, versioned tests** instead of “it felt smart on that one prompt” QA.

## Why Goose?

Think of Goose as **pytest for LLM agents**:

- **Stop guessing** – Encode expectations once, rerun them on every model/version/deploy.
- **See what actually happened** – Rich execution traces, validation results, and per‑step history.
- **Fits your stack** – Wraps your existing agents and tools; no framework rewrite required.
- **Stay in Python** – Pydantic models, type hints, and a straightforward API.

## Install in your project 🚀

Install the core library and CLI from PyPI:

```bash
pip install llm-goose
```

## Writing & running tests ✅

At its core, Goose lets you describe **what a good interaction looks like** and then assert that your
agent and tools actually behave that way.

### 1. Wrap your agent

You provide a callable that takes a query and talks to your model (OpenAI, Bedrock, internal API, …):

```python
from typing import Any

from goose.testing import Goose


def my_agent(query: str) -> dict[str, Any]:
    """Call your LLM here and normalize the response for Goose."""
    ...  # e.g. call OpenAI, Anthropic, or your own router


goose = Goose(my_agent)
```

### 2. Describe expectations & tool usage

Goose cases combine a natural‑language query, human‑readable expectations, and (optionally) the tools
you expect the agent to call. This example is adapted from
`example_tests/agent_behaviour_test.py` and shows an analytical workflow where the agent both
retrieves data and computes aggregates:

```python
from __future__ import annotations

from example_system.models import Transaction
from example_system.tools import calculate_revenue, get_sales_history
from goose.testing import Goose


def test_sales_history_with_revenue_analysis(goose: Goose) -> None:
    """What were sales in October 2025 and the total revenue?"""

    transactions = Transaction.objects.prefetch_related("items__product").all()
    total_revenue = sum(
        item.price_usd * item.quantity
        for txn in transactions
        for item in txn.items.all()
    )

    goose.case(
        query="What were our sales in October 2025 and how much total revenue?",
        expectations=[
            "Agent retrieved sales history for October 2025",
            "Agent calculated total revenue from the retrieved transactions",
            "Response included the sample transaction from October 15",
            f"Response showed total revenue of ${total_revenue:.2f}",
            "Agent used sales history data to compute revenue totals",
        ],
        expected_tool_calls=[get_sales_history, calculate_revenue],
    )
```

In the full example suite, the `goose` fixture comes from `example_tests/conftest.py`, where it wraps
the example agent and seeds sample data using `@fixture` from `goose.testing`.

### 3. Pytest‑inspired style (including failures)

Goose is **pytest‑inspired**: tests are just functions, and you can mix Goose expectations with regular
assertions. That makes intentional failure cases straightforward to express and debug:

```python
from example_system.models import Product
from example_system.tools import get_product_details


def test_failure_assertion_missing_products(goose: Goose) -> None:
    """Intentional failure to verify assertion handling."""

    goose.case(
        query="What's the price of Hiking Boots?",
        expectations=["Agent provided the correct price"],
        expected_tool_calls=[get_product_details],
    )

    # This assertion is designed to fail – fixtures populate products
    assert Product.objects.count() == 0, "Intentional failure: products are populated in fixtures"
```

When you run this test, Goose will surface both expectation mismatches (if any) and the failing
assertion in the same run, just like you’d expect from a testing framework.

### 4. Run tests from the CLI

Use the bundled CLI (installed as the `goose` command) to discover and execute your test modules:

```bash
# execute every test module under example_tests/
goose run example_tests

# list discovered tests without running them
goose run --list example_tests
```

## Example system & jobs API (optional) 🌐

For richer workflows (and the React dashboard), Goose ships an **example Django system** and a
**FastAPI jobs API**. These live in this repo only – they are not installed with the PyPI package – but
you can run them locally for inspiration or internal tooling.

On the dashboard, the **main grid view** shows one card per test in your suite, with a status pill
(`Passed`, `Failed`, `Queued`, `Running`, or `Not Run`), the most recent duration if it has been
executed, and any top‑level error from the last run. Toggling the "only failures" filter collapses the
grid down to just the failing tests so you can quickly see which checks are red, which have never
been executed, and which ones are currently running.

![Dashboard screenshot](images/dashboard_view.png)

When you click into a test, the **detail view** shows a header with the test name, module path,
latest status and duration, plus the original docstring so you remember what the scenario is
meant to cover. Below that, an **execution history** lists each run as a card: you see every
expectation with a green check or red cross, along with the validator's reasoning explaining
why the run was considered a success or failure. For each step, the underlying messages are
rendered as human / AI / tool bubbles, including tool calls and JSON payloads; if something
went wrong mid‑run, the captured error text is shown at the bottom of the card.

![Detail screenshot](images/detail_view.png)

When you install the `api` extra, you get an additional console script:

- `api` – starts the FastAPI job orchestration server

Install with extras:

```bash
pip install "llm-goose[api]"
```

Then launch the service from your project (for example, after wiring Goose into your own system):

```bash
# start the API server (FastAPI + Uvicorn)
api
```

The React dashboard shown in the screenshots lives in this repo under `web/` and is **not** shipped as
part of the PyPI package.

### React dashboard setup 🖥️

The React dashboard is a separate **web application** that talks to the Goose jobs API over HTTP.
It is built with Vite, React, and Tailwind and is designed to be run either locally during
development or deployed as a static site.

Install the published CLI from npm and let it host the built dashboard for you:

```bash
npm install -g @llm-goose/dashboard-cli

# point the dashboard at your jobs API
GOOSE_API_URL="http://localhost:8000" goose-dashboard
```

This starts a small HTTP server (by default on `http://localhost:8001`) that serves the
prebuilt dashboard against whatever Goose API URL you configure.

## License

MIT License – see `LICENSE` for full text.
