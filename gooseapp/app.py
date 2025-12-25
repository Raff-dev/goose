"""Goose application configuration for the example system."""

from __future__ import annotations

from example_system.agent import agent
from example_system.tools import (
    calculate_revenue,
    check_inventory,
    check_weather_async,
    create_sale,
    find_products_by_category,
    get_markdown_demo,
    get_product_details,
    get_sales_history,
    trigger_system_fault,
)
from goose import GooseApp

app = GooseApp(
    tool_groups={
        "Products": [get_product_details, check_inventory, find_products_by_category],
        "Sales": [get_sales_history, calculate_revenue, create_sale],
        "Diagnostics": [trigger_system_fault, get_markdown_demo, check_weather_async],
    },
    reload_targets=["example_system"],
    reload_exclude=["example_system.models"],
    agents=[agent],
)
