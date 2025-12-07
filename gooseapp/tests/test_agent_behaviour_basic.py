"""Basic agent behavior scenarios for simple product queries."""

from __future__ import annotations

from example_system.models import Product, Transaction
from example_system.tools import (
    calculate_revenue,
    check_inventory,
    find_products_by_category,
    get_product_details,
    get_sales_history,
)
from goose.testing import Goose


def test_price_lookup_hiking_boots(goose: Goose) -> None:
    """Simple scenario: What's the price of Hiking Boots?"""
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


# pylint: disable=duplicate-code
def test_inventory_check_hiking_boots(goose: Goose) -> None:
    """Simple scenario: What is the stock for Hiking Boots?"""
    goose.case(
        query="What is the stock for Hiking Boots?",
        expectations=[
            "Agent checked inventory for Hiking Boots",
            "Agent provided stock quantity information",
            "Response was clear about stock levels",
        ],
        expected_tool_calls=[check_inventory],
    )


def test_category_listing_footwear(goose: Goose) -> None:
    """Category listing: Which products are in the Footwear category?"""
    hiking_boots = Product.objects.get(name="Hiking Boots")
    running_shoes = Product.objects.get(name="Running Shoes")
    goose.case(
        query="What products do we have in the Footwear category?",
        expectations=[
            "Agent found products in Footwear category",
            f"Agent listed 'Hiking Boots' (${hiking_boots.price_usd:.2f})",
            f"Agent listed 'Running Shoes' (${running_shoes.price_usd:.2f})",
            "Response included relevant product information like prices",
        ],
        expected_tool_calls=[find_products_by_category],
    )


def test_sales_history_october_15(goose: Goose) -> None:
    """Sales history: Show sales activity for October 15 2025."""

    goose.case(
        query="Show our sales for October 15 2025",
        expectations=[
            "Agent retrieved sales history for the requested date",
            "Response highlighted the transaction on October 15, 2025",
            "Agent included totals or a clear summary of the sale",
        ],
        expected_tool_calls=[get_sales_history],
    )


def test_revenue_summary_october(goose: Goose) -> None:
    """Revenue summary: How much revenue did we make in October 2025?"""

    transactions = list(Transaction.objects.prefetch_related("items__product").all())
    total_revenue = (
        sum(item.price_usd * item.quantity for transaction in transactions for item in transaction.items.all())
        if transactions
        else 0
    )
    goose.case(
        query="How much revenue did we make in October 2025?",
        expectations=[
            "Agent calculated revenue for October 2025",
            f"Agent found the sample transaction totaling ${total_revenue:.2f}",
            "Response included revenue amount and date range",
        ],
        expected_tool_calls=[calculate_revenue],
    )
