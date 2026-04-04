# Testing

Goose is built around behavior tests written as ordinary Python functions plus `goose.case(...)`.

Use the scaffold README's mental model: **think of Goose as pytest for LLM agents.**

## Test discovery

Goose discovers tests from dotted Python targets such as `gooseapp.tests`:

```bash
goose test list
goose test list gooseapp.tests
goose test run
goose test run gooseapp.tests
goose test run -v gooseapp.tests
```

Discovery rules come from `goose/testing/discovery.py`:

- test modules must start with `test_` or `tests_`
- test functions must start with `test_`
- package targets are walked recursively
- function order inside a module follows source line order

That means these all work:

- `goose test run gooseapp.tests`
- `goose test run gooseapp.tests.test_agent_behaviour_basic`
- `goose test run gooseapp.tests.test_agent_behaviour_basic.test_price_lookup_hiking_boots`

## Anatomy of `goose.case(...)`

This is the core shape, using a real example from `gooseapp/tests/test_agent_behaviour_basic.py`:

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
            "Response was direct and factual without unnecessary information",
        ],
        expected_tool_calls=[get_product_details],
    )
```

The three fields do different jobs:

- `query` - the user message sent to your agent
- `expectations` - natural-language assertions validated against the response
- `expected_tool_calls` - an optional tool audit using the actual tool callables

## Writing good expectations

Good expectations are flexible enough for LLM variation, but still specific enough to fail for the right reason.

Prefer:

- one assertion per expectation
- observable outcomes
- concrete facts from your fixture data

Avoid:

- `"Agent responded appropriately"`
- `"Agent handled the request well"`
- `"Agent found the product and gave the price and was helpful"`

Those examples are bad for the same reasons documented in the scaffold README:

- vague
- subjective
- multiple assertions packed into one line

Better patterns from the repo:

```python
expectations=[
    "Agent checked inventory for Hiking Boots",
    "Agent provided stock quantity information",
    "Response was clear about stock levels",
]
```

```python
expectations=[
    "Agent retrieved sales history for October 2025",
    f"Response showed total revenue of ${total_revenue:.2f}",
]
```

## `expected_tool_calls`

Use `expected_tool_calls` when the tool path matters.

Rules that match the current implementation and example suite:

- pass the actual tool functions, not strings
- keep the list in execution order
- do not repeat tool assertions in `expectations`
- omit it when the exact tool path is not important

Real examples:

```python
expected_tool_calls=[get_product_details]
expected_tool_calls=[find_products_by_category, check_inventory]
expected_tool_calls=[get_sales_history, calculate_revenue]
```

The failure suite in `gooseapp/tests/test_agent_behaviour_failures.py` is worth studying because it shows what
breaks:

- missing expected tools
- extra expected tools
- extra actual tool calls

## Fixtures and `conftest.py`

Fixtures are registered with `@fixture(...)` in `gooseapp/conftest.py`.

Real example:

```python
@fixture(autouse=True)
def setup_data() -> None:
    ...


@fixture(name="goose")
def goose_fixture() -> Goose:
    return Goose(
        agent_query_func=query,
        hooks=DjangoTestHooks(),
        validator_model="gpt-4o-mini",
    )
```

What this gives you:

- a named `goose` fixture injected by parameter name
- optional `autouse=True` setup fixtures
- dependency injection between fixtures by argument name

Every discovery pass clears and rebuilds the fixture registry, then re-imports `gooseapp.conftest`. Keep your test
fixtures there so reloads behave predictably.

## Lifecycle hooks

If your tests need setup and teardown around each case, attach `hooks=` when you build the Goose fixture.

The repo example uses `DjangoTestHooks()`:

```python
return Goose(
    agent_query_func=query,
    hooks=DjangoTestHooks(),
    validator_model="gpt-4o-mini",
)
```

`DjangoTestHooks` runs Django's test environment before each case and flushes it afterward. If you need custom
behavior, implement your own `TestLifecycleHooks` with `pre_test(...)` and `post_test(...)`.

## Debugging failures

Start narrow:

```bash
goose test list
goose test run gooseapp.tests.test_agent_behaviour_basic
goose test run -v gooseapp.tests.test_agent_behaviour_basic.test_price_lookup_hiking_boots
```

Use `-v` when you need the transcript, agent reply, and tool activity in the terminal.

The example suite intentionally demonstrates several failure classes:

- expectation mismatch
- tool audit mismatch
- assertion failure after a passing case
- runtime error after a passing case
- tool exception before the agent can finish cleanly

If you want the same information in the browser, run the dashboard and inspect the trace in
[`dashboard.md`](dashboard.md).
