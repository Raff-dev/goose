"""Goose application configuration.

This module defines your GooseApp instance, which is the central configuration
for the Goose testing framework. It tells Goose:

    1. What tools your agent uses (for display in the dashboard)
    2. What modules to hot-reload when you make changes
    3. What modules to exclude from reloading

Example with a LangChain agent:
    from my_agent.tools import search_products, get_order_status, create_ticket
    from my_agent.data import PRODUCTS, ORDERS

    app = GooseApp(
        tools=[search_products, get_order_status, create_ticket],
        reload_targets=["my_agent"],
        reload_exclude=["my_agent.data"],  # Skip reloading static data
    )
"""

from goose import GooseApp

# =============================================================================
# Tool Registration
# =============================================================================
# Import your LangChain @tool decorated functions here.
# These will be displayed in the Goose dashboard for reference.
#
# Example:
#     from my_agent.tools import (
#         search_products,
#         get_order_status,
#         create_support_ticket,
#     )

# =============================================================================
# Application Configuration
# =============================================================================

app = GooseApp(
    # -------------------------------------------------------------------------
    # tools: List of LangChain @tool decorated functions
    # -------------------------------------------------------------------------
    # Register your agent's tools here. Goose will display them in the
    # dashboard and use them for tool-related assertions in tests.
    #
    # Example:
    #     tools=[search_products, get_order_status, create_support_ticket],
    tools=[],
    # -------------------------------------------------------------------------
    # reload_targets: List of module name prefixes to hot-reload
    # -------------------------------------------------------------------------
    # When you make changes to your agent code, Goose will reload these
    # modules before running the next test. This enables rapid iteration
    # without restarting the server.
    #
    # Example:
    #     reload_targets=["my_agent", "shared_utils"],
    #
    # Note: "gooseapp" is always included automatically.
    reload_targets=[],
    # -------------------------------------------------------------------------
    # reload_exclude: List of module name prefixes to skip during reload
    # -------------------------------------------------------------------------
    # Some modules should not be reloaded (e.g., static data, database
    # connections, expensive initializations). List them here.
    #
    # Example:
    #     reload_exclude=["my_agent.data", "my_agent.db"],
    reload_exclude=[],
)
