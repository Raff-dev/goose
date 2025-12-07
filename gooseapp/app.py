"""Goose application configuration for the example system."""

from __future__ import annotations

from example_system.tools import (
    calculate_revenue,
    check_inventory,
    create_sale,
    find_products_by_category,
    get_product_details,
    get_sales_history,
    trigger_system_fault,
)
from goose import GooseApp

app = GooseApp(
    tools=[
        get_product_details,
        check_inventory,
        get_sales_history,
        calculate_revenue,
        find_products_by_category,
        create_sale,
        trigger_system_fault,
    ],
    reload_targets=["example_system"],
    reload_exclude=["example_system.models"],
)
