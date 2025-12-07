"""Workflow-oriented agent behavior tests."""

from __future__ import annotations

from example_system.models import Product, ProductInventory, Transaction
from example_system.tools import (
    calculate_revenue,
    check_inventory,
    create_sale,
    find_products_by_category,
    get_sales_history,
)
from goose.testing import Goose


def test_combined_category_inventory_workflow(goose: Goose) -> None:
    """Complex workflow: What Footwear products do we have in stock?"""

    goose.case(
        query="What Footwear products do we have in stock?",
        expectations=[
            "Agent found products in Footwear category",
            "Agent checked inventory for the footwear products",
            "Response provided product names and their stock levels",
            "Agent used category search results to check inventory",
        ],
        expected_tool_calls=[find_products_by_category, check_inventory],
    )


def test_sale_then_inventory_update(goose: Goose) -> None:
    """Complex workflow: Sell 2 Hiking Boots and report the remaining stock."""

    transactions_before = Transaction.objects.count()
    hiking_boots = Product.objects.get(name="Hiking Boots")
    inventory = ProductInventory.objects.filter(product=hiking_boots).first()
    assert inventory is not None, "Expected inventory record for Hiking Boots"
    stock_before = inventory.stock

    goose.case(
        query="Sell 2 pairs of Hiking Boots to John Doe and then tell me how many we have left",
        expectations=[
            "Agent created a sale transaction for 2 Hiking Boots to John Doe",
            "Agent then checked remaining inventory after the sale",
            "Response confirmed the sale was processed",
            "Response provided updated stock information",
        ],
        expected_tool_calls=[create_sale, check_inventory],
    )

    transactions_after = Transaction.objects.count()
    assert (
        transactions_after == transactions_before + 1
    ), f"Expected 1 new transaction, got {transactions_after - transactions_before}"

    inventory_after = ProductInventory.objects.filter(product=hiking_boots).first()
    assert inventory_after is not None, "Expected inventory record after sale"
    assert inventory_after.stock == stock_before - 2, f"Expected stock {stock_before - 2}, got {inventory_after.stock}"


def test_sales_history_with_revenue_analysis(goose: Goose) -> None:
    """Complex workflow: What were sales in October 2025 and the total revenue?"""

    transactions = Transaction.objects.prefetch_related("items__product").all()
    total_revenue = sum(item.price_usd * item.quantity for txn in transactions for item in txn.items.all())

    goose.case(
        query="What were our sales in October 2025 and how much total revenue?",
        expectations=[
            "Agent retrieved sales history for October 2025",
            "Agent calculated total revenue from the retrieved transactions",
            "Response included the sample transaction from October 15",
            f"Response showed total revenue of ${total_revenue:.2f}",
            "Agent used sales history data to compute revenue totals",
        ],
        expected_tool_calls=[get_sales_history, calculate_revenue],
    )
