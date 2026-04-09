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
    # tools: List of tool callables to show in the dashboard
    # -------------------------------------------------------------------------
    # Register your app's tools here. Goose will display them in the dashboard.
    # Import them from your own code, e.g.:
    #     from my_agent.tools import search_products, get_product_details
    #
    # Best results come from LangChain-style tools (`@tool`, StructuredTool,
    # etc.) that expose `name`, `description`, and optionally `args_schema`.
    # Plain callables also work, but with thinner metadata in the Tooling view.
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
    # agents: List of agent objects for live chat
    # -------------------------------------------------------------------------
    # Register agent objects here to enable interactive chat in the dashboard.
    # Import them from your own code, e.g.:
    #     from my_agent.chat import support_agent
    #
    # Each agent must have a unique `name`.
    #
    # Goose live chat supports:
    #   - Goose-native agents with `astream_goose(conversation=..., messages=...)`
    #   - legacy LangChain-style agents exposing:
    #       astream({"messages": messages}, stream_mode="messages")
    #
    # If you want the Goose-native protocol explicitly, see:
    #     goose.chatting.agent_protocol.GooseChatAgent
    #     goose.chatting.agent_protocol.GooseAgentEvent
    #
    # Example:
    #     agents=[
    #         support_agent,
    #         billing_agent,
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
