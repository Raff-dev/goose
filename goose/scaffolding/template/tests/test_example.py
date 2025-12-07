"""Example Goose tests demonstrating common patterns.

This file shows how to write behavioral tests for your LLM agent.
Delete or modify these examples once you understand the patterns.

Test structure:
    1. Define a function starting with `test_`
    2. Receive a Goose fixture as a parameter (matching your fixture name)
    3. Use goose.case() to send a query and define expectations

The goose.case() method:
    query: str
        The message to send to your agent.

    expectations: list[str]
        Natural language descriptions of what the response should contain.
        An LLM validator checks if the agent's response meets these.

    expected_tool_calls: list[BaseTool] | None
        Optional list of LangChain tools the agent should have called.
        Pass the actual tool functions, not strings.

Example:
    def test_weather_query(goose: Goose) -> None:
        goose.case(
            query="What's the weather in Paris?",
            expectations=[
                "Agent provides weather information for Paris",
                "Response includes temperature",
            ],
            expected_tool_calls=[get_weather],
        )
"""

from goose.testing import Goose

# =============================================================================
# Basic Test Example
# =============================================================================


def test_agent_responds_helpfully(goose: Goose) -> None:
    """Test that the agent provides a helpful response.

    This is a minimal example showing the goose.case() API.
    The expectations are validated by an LLM, so they can be
    written in natural language.
    """
    goose.case(
        query="Hello, what can you help me with?",
        expectations=[
            "Agent responds with a greeting or acknowledgment",
            "Agent describes its capabilities or offers assistance",
        ],
    )


# =============================================================================
# Tool Call Assertions
# =============================================================================


def test_agent_uses_correct_tool(goose: Goose) -> None:
    """Test that the agent calls the expected tool.

    Use expected_tool_calls to verify the agent used specific tools.
    Import your actual tool functions and pass them in the list.

    Example with tools:
        from my_agent.tools import search_products, get_inventory

        def test_product_search(goose: Goose) -> None:
            goose.case(
                query="Find running shoes under $100",
                expectations=["Agent found relevant products"],
                expected_tool_calls=[search_products],
            )
    """
    goose.case(
        query="Search for something",
        expectations=[
            "Agent attempts to search or asks for clarification",
        ],
        # expected_tool_calls=[your_search_tool],  # Uncomment with your tool
    )


# =============================================================================
# Complex Workflow Test
# =============================================================================


def test_multi_step_workflow(goose: Goose) -> None:
    """Test a workflow that involves multiple steps.

    Expectations can describe the full workflow, including:
    - What tools should be called and in what order
    - What information should be in the response
    - What side effects should occur (check with assertions after)

    Example from a sales agent:
        def test_sale_workflow(goose: Goose) -> None:
            initial_count = Order.objects.count()

            goose.case(
                query="Sell 2 Hiking Boots to John Doe",
                expectations=[
                    "Agent created a sale transaction",
                    "Response confirms the sale was processed",
                    "Response includes order details",
                ],
                expected_tool_calls=[check_inventory, create_sale],
            )

            # Verify side effects
            assert Order.objects.count() == initial_count + 1
    """
    goose.case(
        query="Help me complete a multi-step task",
        expectations=[
            "Agent understands the request",
            "Agent provides step-by-step guidance or completes the task",
        ],
    )
