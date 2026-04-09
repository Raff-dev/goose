# Testing

Goose is built around ordinary Python test functions plus `goose.case(...)`.

Use the scaffold README's mental model: **think of Goose as pytest for LLM agents.**

If you want the shortest integration path, start with [`getting-started.md`](getting-started.md) first and come back to
this page as reference.

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
- `expected_tool_calls` - an optional tool audit using tool names

## The query function contract behind `goose.case(...)`

`goose.case(...)` only defines the test. When the case executes, Goose takes the `query=` string and passes it into
the callable you registered as `agent_query_func` in `gooseapp/conftest.py`.

Example:

```python
from goose.testing.models.messages import AgentResponse, Message, ToolCall


def query(message: str) -> AgentResponse:
    result = run_my_agent(message)

    return AgentResponse(
        messages=[
            Message(
                type="ai",
                content=result.text,
                tool_calls=[
                    ToolCall(
                        name="get_product_details",
                        args={"product_name": "Hiking Boots"},
                    )
                ],
            )
        ]
    )
```

What Goose passes in:

- `message: str` - the exact user prompt from `goose.case(query=...)`

What Goose expects back:

- `AgentResponse(messages=[...])`
- at least one final `Message(type="ai", content="...")`
- `tool_calls=[...]` on AI messages if you want `expected_tool_calls=[...]` to work
- optional `Message(type="tool", ...)` entries if you want richer transcripts

The human message is optional in the return value because Goose already knows the test input. The most important pieces
are the final AI message and any tool calls you want audited.

If your app already returns a LangChain-style payload, normalize it instead of rebuilding the structure manually:

```python
from goose.testing.models.messages import AgentResponse


def query(message: str) -> AgentResponse:
    raw_response = my_langchain_agent.invoke({"messages": [{"role": "user", "content": message}]})
    return AgentResponse.from_langchain(raw_response)
```

## Fixtures and `conftest.py`

Fixtures are registered with `@fixture(...)` in `gooseapp/conftest.py`.

Simple example:

```python
from goose.testing import Goose, fixture


@fixture()
def goose() -> Goose:
    return Goose(
        agent_query_func=query,
        validator_model="gpt-4o-mini",
    )
```

### Exact matching rule

This is the actual behavior from `goose/testing/fixtures.py`:

- fixture injection resolves by **parameter name**
- `@fixture(name="...")` overrides the registered name
- if `name=` is omitted, Goose uses the fixture function name
- the type annotation is helpful for readers, but matching does **not** happen by type

So this:

```python
@fixture(name="goose")
def goose_fixture() -> Goose:
    ...


def test_price_lookup(goose: Goose) -> None:
    ...
```

works because the test parameter is named `goose`.

### Multiple Goose fixtures

You can register multiple Goose fixtures for different agents or environments:

```python
@fixture(name="sales_goose")
def sales_goose_fixture() -> Goose:
    return Goose(agent_query_func=query_sales_agent)


@fixture(name="staging_goose")
def staging_goose_fixture() -> Goose:
    return Goose(agent_query_func=query_staging_agent)
```

Then opt into the right fixture by parameter name:

```python
def test_sales_quote_flow(sales_goose: Goose) -> None:
    sales_goose.case(
        query="Prepare a quote for hiking boots",
        expectations=["Agent prepares a quote for hiking boots"],
    )
```

Goose also supports:

- `autouse=True` setup fixtures
- dependency injection between fixtures by argument name

Example:

```python
@fixture(autouse=True)
def setup_data() -> None:
    ...


@fixture()
def goose() -> Goose:
    return Goose(
        agent_query_func=query,
        hooks=DjangoTestHooks(),
        validator_model="gpt-4o-mini",
    )
```

Every discovery pass clears and rebuilds the fixture registry, then re-imports `gooseapp.conftest`. Keep your test
fixtures there so reloads behave predictably.

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

What the current implementation validates:

- expected tool calls are compared by **tool name**
- order is **not** validated
- extra actual tool calls are allowed
- the test only fails when expected tools are missing

Accepted input shapes include:

- actual tool callables
- plain tool name strings
- objects with a non-empty `.name`
- OpenAI-style tool dicts with `name` or `function.name`

Examples:

```python
expected_tool_calls=[get_product_details]
expected_tool_calls=["check_inventory"]
expected_tool_calls=[find_products_by_category, check_inventory]
```

When the exact tool path is not important, omit `expected_tool_calls` and keep expectations focused on the user-visible
outcome.

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
- missing expected tools
- assertion failure after a passing case
- runtime error after a passing case
- tool exception before the agent can finish cleanly

If you want the same information in the browser, run the dashboard and inspect the trace in
[`dashboard.md`](dashboard.md).
