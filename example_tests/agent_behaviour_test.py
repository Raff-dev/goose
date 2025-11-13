"""Test cases for agent behavior with analytical tools."""

from __future__ import annotations

from example_system.models import Product, ProductInventory, Transaction
from example_system.tools import (
    calculate_revenue,
    check_inventory,
    create_sale,
    find_products_by_category,
    get_product_details,
    get_sales_history,
    trigger_system_fault,
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
        expected_tool_calls=None,
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
        expected_tool_calls=[check_inventory, create_sale],
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

    transactions = list(Transaction.objects.prefetch_related("items__product").all())
    total_revenue = (
        sum(item.price_usd * item.quantity for transaction in transactions for item in transaction.items.all())
        if transactions
        else 0
    )
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


# Intentional failure cases live at the bottom for quick access during debugging.
def test_failure_expectation_inventory_stock(goose: Goose) -> None:
    """Intentional failure: expectation should not match actual agent behaviour."""

    goose.case(
        query="What is the stock for Hiking Boots?",
        expectations=[
            "Agent reported that Hiking Boots are out of stock",  # known incorrect expectation
            "Agent checked inventory for Hiking Boots",
            "Agent provided stock quantity information",
        ],
        expected_tool_calls=[check_inventory],
    )


def test_failure_tool_audit_inventory_stock(goose: Goose) -> None:
    """Intentional failure: expectations pass but tool audit should fail."""

    goose.case(
        query="What is the stock for Hiking Boots?",
        expectations=[
            "Agent checked inventory for Hiking Boots",
            "Agent provided stock quantity information",
        ],
        expected_tool_calls=[check_inventory, get_sales_history],  # extra tool never invoked
    )


def test_failure_assertion_missing_products(goose: Goose) -> None:
    """Intentional failure: manual assertion to verify runner surfaces assertion errors."""

    goose.case(
        query="What's the price of Hiking Boots?",
        expectations=["Agent provided the correct price"],
        expected_tool_calls=[get_product_details],
    )

    assert Product.objects.count() == 0, "Intentional failure: products are populated in fixtures"


def test_failure_runtime_after_sales_report(goose: Goose) -> None:
    """Intentional failure: raise runtime error after successful agent response."""

    goose.case(
        query="Show October 2025 sales and revenue totals.",
        expectations=[
            "Agent retrieved sales history for October 2025",
            "Agent provided total revenue",
        ],
        expected_tool_calls=[get_sales_history, calculate_revenue],
    )

    raise RuntimeError("Intentional failure: simulate unexpected error after case execution")


def test_failure_tool_runtime_trigger_system_fault(goose: Goose) -> None:
    """Intentional failure: tool raises an exception that propagates to the agent."""

    goose.case(
        query="Run the trigger system fault diagnostic and confirm the system is healthy.",
        expectations=[
            "Agent confirmed the system fault diagnostic succeeded",
        ],
        expected_tool_calls=[trigger_system_fault],
    )
