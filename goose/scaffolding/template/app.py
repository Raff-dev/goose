"""Goose application configuration.

This module defines your GooseApp instance, which is the central configuration
for the Goose testing framework.
"""

from goose import GooseApp

# =============================================================================
# Application Configuration
# =============================================================================

app = GooseApp(
    # -------------------------------------------------------------------------
    # tools: List of LangChain @tool decorated functions
    # -------------------------------------------------------------------------
    # Register your agent's tools here. Goose will display them in the dashboard.
    #
    # Example:
    #     tools=[search_products, get_product_details, get_order_status],
    #
    # For grouped display, use tool_groups instead (cannot use both):
    #     tool_groups={
    #         "Products": [search_products, get_product_details],
    #         "Orders": [get_order_status, cancel_order],
    #     },
    tools=[],
    # -------------------------------------------------------------------------
    # agents: List of agent configurations for chatting
    # -------------------------------------------------------------------------
    # Register your agents here to enable interactive chat in the dashboard.
    # Each agent config needs: name (str), get_agent (callable), models (list).
    # The get_agent callable receives a model name and returns a LangChain agent.
    #
    # Example:
    #     agents=[
    #         {
    #             "name": "Customer Support Agent",
    #             "get_agent": get_agent,  # def get_agent(model: str) -> Agent
    #             "models": ["gpt-4o-mini", "gpt-4o"],
    #         },
    #     ],
    agents=[],
    # -------------------------------------------------------------------------
    # reload_targets: List of module name prefixes to hot-reload
    # -------------------------------------------------------------------------
    # When you make changes to your agent code, Goose will reload these
    # modules before running the next test. This enables rapid iteration
    # without restarting the server.
    #
    # Note: "gooseapp" is always included automatically.
    #
    # Example:
    #     reload_targets=["my_agent", "shared_utils"],
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
