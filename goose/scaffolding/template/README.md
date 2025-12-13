# Goose - LLM Agent Testing Framework

**Think of Goose as pytest for LLM agents.**

## Quick Links

- 📦 [PyPI Package](https://pypi.org/project/llm-goose/)
- 🐙 [GitHub Repository](https://github.com/Raff-dev/goose)
- 🎨 [Dashboard (npm)](https://www.npmjs.com/package/goose-dashboard)

## Getting Started

```bash
# Run tests
goose test run gooseapp.tests

# Run tests with verbose output
goose test run -v gooseapp.tests

# List tests without running
goose test list gooseapp.tests

# Start the API server (hot-reload always enabled)
goose api

# Run the dashboard (separate terminal)
goose-dashboard
```

## Dashboard Features

The Goose dashboard provides three main views:

### Testing View
Run and monitor your agent tests with real-time results, detailed tool call inspection, and conversation thread visualization.

### Tooling View
Interactively test your agent's tools in isolation. Select a tool, fill in parameters, and see the output instantly.

### Chat View
Chat with your agents directly. Configure agents in `gooseapp/app.py`:

```python
from goose import GooseApp
from my_agent.agent import get_agent

app = GooseApp(
    agents=[
        {
            "name": "My Agent",
            "get_agent": get_agent,  # def get_agent(model: str) -> Agent
            "models": ["gpt-4o-mini", "gpt-4o"],
        },
    ],
)
```

---

## Writing Tests Guidelines

### Be Generic Enough, Yet Specific Enough

Agent outputs vary between runs since LLMs are non-deterministic. Expectations need to be:
- **Flexible enough** to avoid flakiness
- **Specific enough** to validate meaningful behavior
- **Focused on verifiable outcomes** rather than exact wording or execution details

### Tool Calls vs Expectations Separation

If you specify `expected_tool_calls=[tool_name]`, there's no need to add an expectation that the agent called the tool - that's already being verified.

### One Assertion Per Expectation

Avoid combining multiple assertions. Each expectation should validate one thing.

**Good:**
```python
expectations=[
    "Agent created a transaction for Hiking Boots",
    "Agent provided information about Running Shoes including price",
    "Response included the customer name John Doe",
]
```

**Bad:**
```python
expectations=[
    "Agent created a transaction and provided product info and mentioned the customer",
]
```

### Focus on Observable Behavior

Test what the agent communicates, not how it thinks internally. Focus on the outcome, not the path it took.

### Avoid Subjective or Fuzzy Language

Avoid words like: "appropriate", "good", "well", "properly", "correctly", "like"

**Bad:**
```python
expectations=[
    "Agent responded appropriately to the query",
    "Agent handled the request well",
    "Agent properly processed the order",
]
```

**Good:**
```python
expectations=[
    "Agent provided the price of Hiking Boots ($129.99)",
    "Agent listed all products in the Footwear category",
    "Agent confirmed the transaction was created for 2 items",
]
```

---

## Examples

### Bad Expectations (Antipatterns)

```python
def test_product_query_bad(goose: Goose) -> None:
    """Antipattern: vague, subjective, and redundant expectations."""
    goose.case(
        query="What's the price of Hiking Boots?",
        expectations=[
            "Agent called the right tool",  # Redundant - use expected_tool_calls
            "Agent responded appropriately",  # Vague - what does "appropriately" mean?
            "Agent did a good job answering",  # Subjective - not verifiable
            "Agent found the product and gave the price and was helpful",  # Multiple assertions
        ],
        expected_tool_calls=[get_product_details],
    )
```

### Good Expectations (Following Best Practices)

```python
def test_product_query_good(goose: Goose) -> None:
    """Best practice: specific, verifiable, one assertion per expectation."""
    hiking_boots = Product.objects.get(name="Hiking Boots")
    goose.case(
        query="What's the price of Hiking Boots?",
        expectations=[
            f"Agent provided the correct price (${hiking_boots.price_usd:.2f})",
            "Agent identified the product as 'Hiking Boots'",
            "Response was direct and factual",
        ],
        expected_tool_calls=[get_product_details],
    )
```

---

## Reference

Check `gooseapp/tests/` for existing tests that demonstrate proven patterns for writing stable, meaningful expectations.
