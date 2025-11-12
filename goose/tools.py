"""Tool re-exports for the Goose Outfitters agent."""

from __future__ import annotations

from example_system.tools import TOOLS as EXAMPLE_TOOLS  # noqa: F401 re-exported names
from example_system.tools import (
    calculate_revenue,
    check_inventory,
    create_sale,
    find_products_by_category,
    get_product_details,
    get_sales_history,
)

TOOLS = list(EXAMPLE_TOOLS)

__all__ = [
    "calculate_revenue",
    "check_inventory",
    "create_sale",
    "find_products_by_category",
    "get_product_details",
    "get_sales_history",
    "TOOLS",
]
