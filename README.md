<h1 align="center">LLM Goose 🪿</h1>

<p align="center">
  <strong>LLM-powered testing for LLM agents — define expectations as you'd describe them to a human</strong>
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
Goose is a <strong>Python library, CLI, and web dashboard</strong> that helps developers build and iterate on LLM agents faster.<br>
Write tests in Python, run them from the terminal or dashboard, and instantly see what went wrong when things break.
</p>

<p align="center">
Currently designed for LangChain-based agents, with plans for framework-agnostic support.
</p>

## Why Goose?

Think of Goose as **pytest for LLM agents**:

- **Natural language expectations** – Describe what should happen in plain English; an LLM validator checks if the agent delivered.
- **Tool call assertions** – Verify your agent called the right tools, not just that it sounded confident.
- **Full execution traces** – See every tool call, response, and validation result in the web dashboard.
- **Pytest-style fixtures** – Reuse agent setup across tests with `@fixture` decorators.
- **Hot-reload during development** – Edit your agent code, re-run tests instantly without restarting the server.

---

<p align="center">
  <img src="https://raw.githubusercontent.com/Raff-dev/goose/main/images/dashboard_view.png" alt="Dashboard screenshot" width="80%">
</p>

<p align="center">
  <img src="https://raw.githubusercontent.com/Raff-dev/goose/main/images/detail_view.png" alt="Detail screenshot" width="80%">
</p>

## Install 🚀

```bash
pip install llm-goose
npm install -g @llm-goose/dashboard-cli
```

### CLI

```bash
# Initialize a new gooseapp/ project structure
goose init

# run tests from the terminal
goose test run gooseapp.tests

# list tests without running them
goose test list gooseapp.tests

# add -v / --verbose to stream detailed steps
goose test run -v gooseapp.tests
```

### API & Dashboard

```bash
# Start the dashboard (auto-discovers gooseapp/ in current directory)
goose api

# Custom host and port
goose api --host 0.0.0.0 --port 3000

# run the dashboard (connects to localhost:8730 by default)
goose-dashboard

# or point the dashboard at a custom API URL
GOOSE_API_URL="http://localhost:8730" goose-dashboard
```

### GooseApp Configuration

Run `goose init` to create a `gooseapp/` folder with centralized configuration:

```python
# gooseapp/app.py
from goose import GooseApp
from my_agent.tools import get_weather, get_forecast

app = GooseApp(
    tools=[get_weather, get_forecast],  # Tools visible in the Tooling dashboard
    reload_targets=["my_agent"],         # Modules to hot-reload during development
    reload_exclude=["my_agent.data"],    # Modules to skip during reload
)
```

## Quick Start: Minimal Example 🏃‍♂️

Here's a complete, runnable example of testing an LLM agent with Goose. This creates a simple weather assistant agent and tests it.

### 1. Set up your agent

Create `my_agent.py`:

```python
from typing import Any

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from goose.testing.models.messages import AgentResponse

load_dotenv()

@tool
def get_weather(location: str) -> str:
    """Get the current weather for a given location."""
    return f"The weather in {location} is sunny and 75°F."

agent = create_agent(
    model="gpt-4o-mini",
    tools=[get_weather],
    system_prompt="You are a helpful weather assistant",
)

def query_weather_agent(question: str) -> AgentResponse:
    """Query the agent and return a normalized response."""
    result = agent.invoke({"messages": [HumanMessage(content=question)]})
    return AgentResponse.from_langchain(result)
```

### 2. Set up fixtures

Create `tests/conftest.py`:

```python
from langchain_openai import ChatOpenAI

from goose.testing import Goose, fixture
from my_agent import query_weather_agent

@fixture(name="weather_goose")  # name is optional - defaults to func name
def weather_goose_fixture() -> Goose:
    """Provide a Goose instance wired up to the sample LangChain agent."""

    return Goose(
        agent_query_func=query_weather_agent,
        validator_model=ChatOpenAI(model="gpt-4o-mini"),
    )
```


### 3. Write a test

Create `tests/test_weather.py`. Fixture will be injected into recognized test functions. Test function and file names need to start with `test_` in order to be discovered.

```python
from goose.testing import Goose
from my_agent import query_weather_agent

def test_weather_query(weather_goose: Goose) -> None:
    """Test that the agent can answer weather questions."""

    weather_goose.case(
        query="What's the weather like in San Francisco?",
        expectations=[
            "Agent provides weather information for San Francisco",
            "Response mentions sunny weather and 75°F",
        ],
        expected_tool_calls=[get_weather],
    )
```



### 4. Run the test

```bash
goose test run tests
```

That's it! Goose will run your agent, check that it called the expected tools, and validate the response against your expectations.

## Writing tests

At its core, Goose lets you describe **what a good interaction looks like** and then assert that your
agent and tools actually behave that way.

### Pytest-inspired syntax

Goose cases combine a natural‑language query, human‑readable expectations, and (optionally) the tools
you expect the agent to call. This example is adapted from
`example_tests/agent_behaviour_test.py` and shows an analytical workflow where the agent both
retrieves data and creates records:


```python
def test_sale_then_inventory_update(goose_fixture: Goose) -> None:
    """Complex workflow: Sell 2 Hiking Boots and report the remaining stock."""

    count_before = Transaction.objects.count()
    inventory = ProductInventory.objects.get(product__name="Hiking Boots")
    assert inventory is not None, "Expected inventory record for Hiking Boots"

    goose_fixture.case(
        query="Sell 2 pairs of Hiking Boots to John Doe and then tell me how many we have left",
        expectations=[
            "Agent created a sale transaction for 2 Hiking Boots to John Doe",
            "Agent then checked remaining inventory after the sale",
            "Response confirmed the sale was processed",
            "Response provided updated stock information",
        ],
        expected_tool_calls=[check_inventory, create_sale],
    )

    count_after = Transaction.objects.count()
    inventory_after = ProductInventory.objects.get(product__name="Hiking Boots")

    assert count_after == count_before + 1, f"Expected 1 new transaction, got {count_after - count_before}"
    assert inventory_after is not None, "Expected inventory record after sale"
    assert inventory_after.stock == inventory.stock - 2, f"Expected stock {inventory.stock - 2}, got {inventory_after.stock}"
```

### Custom lifecycle hooks

You can use existing lifecycle hooks or implement yours to suit your needs.
Hooks are invoked before a test starts and after it finishes.
This lets you setup your environment and teardown it afterwards.

```python
from goose.testing.hooks import TestLifecycleHook

class MyLifecycleHooks(TestLifecycleHook):
    """Suite and per-test lifecycle hooks invoked around Goose executions."""

    def pre_test(self, definition: TestDefinition) -> None:
        """Hook invoked before a single test executes."""
        setup()

    def post_test(self, definition: TestDefinition) -> None:
        """Hook invoked after a single test completes."""
        teardown()


# tests/conftest.py
from langchain_openai import ChatOpenAI

from goose.testing import Goose, fixture
from my_agent import query

@fixture()
def goose_fixture() -> Goose:
    """Provide a Goose instance wired up to the sample LangChain agent."""

    return Goose(
        agent_query_func=query,
        validator_model=ChatOpenAI(model="gpt-4o-mini"),
        hooks=MyLifecycleHooks(),
    )
```

## License

MIT License – see `LICENSE` for full text.
