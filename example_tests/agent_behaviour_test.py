"""Test cases for agent behavior with analytical tools."""

import asyncio

import pytest

from example_system.models import Product, ProductInventory, Transaction
from example_system.tools import (
    calculate_revenue,
    check_inventory,
    create_sale,
    find_products_by_category,
    get_product_details,
    get_sales_history,
)
from goose.testing import Goose, ValidationResult

pytestmark = pytest.mark.django_db(transaction=True)


def test_simple_question_1_product_price(goose_fixture: Goose):
    """Test: What's the price of Hiking Boots? (Simple - single tool)"""
    hiking_boots = Product.objects.get(name="Hiking Boots")
    case = goose_fixture.case(
        query="What's the price of Hiking Boots?",
        expectations=[
            f"Agent provided the correct price (${hiking_boots.price_usd:.2f})",
            "Agent identified the product correctly as 'Hiking Boots'",
            "Response was direct and factual without unnecessary information",
        ],
        expected_tool_calls=[get_product_details],
    )
    return case


def test_simple_question_2_inventory_check(goose_fixture: Goose):
    """Test: What is the stock for Hiking Boots? (Simple - single tool)"""
    case = goose_fixture.case(
        query="What is the stock for Hiking Boots?",
        expectations=[
            "Agent checked inventory for Hiking Boots",
            "Agent provided stock quantity information",
            "Response was clear about stock levels",
        ],
        expected_tool_calls=[check_inventory],
    )
    return case


def test_normal_question_1_find_by_category(goose_fixture: Goose):
    """Test: What products do we have in the Footwear category? (Normal - single tool)"""
    hiking_boots = Product.objects.get(name="Hiking Boots")
    running_shoes = Product.objects.get(name="Running Shoes")
    case = goose_fixture.case(
        query="What products do we have in the Footwear category?",
        expectations=[
            "Agent found products in Footwear category",
            f"Agent listed 'Hiking Boots' (${hiking_boots.price_usd:.2f})",
            f"Agent listed 'Running Shoes' (${running_shoes.price_usd:.2f})",
            "Response included relevant product information like prices",
        ],
        expected_tool_calls=[find_products_by_category],
    )
    return case


def test_normal_question_2_sales_history(goose_fixture: Goose):
    """Test: Show our sales activity for mid-October 2025. (Normal - single tool)"""
    case = goose_fixture.case(
        query="Show our sales for October 15 2025",
        expectations=[
            "Agent retrieved sales history for the requested date",
            "Response highlighted the transaction on October 15, 2025",
            "Agent included totals or a clear summary of the sale",
        ],
        expected_tool_calls=[get_sales_history],
    )
    return case


def test_normal_question_3_revenue_calculation(goose_fixture: Goose):
    """Test: How much revenue did we make in October 2025? (Normal - single tool)"""
    transactions = list(Transaction.objects.prefetch_related("items__product").all())
    total_revenue = (
        sum(item.price_usd * item.quantity for transaction in transactions for item in transaction.items.all())
        if transactions
        else 0
    )
    case = goose_fixture.case(
        query="How much revenue did we make in October 2025?",
        expectations=[
            "Agent calculated revenue for October 2025",
            f"Agent found the sample transaction totaling ${total_revenue:.2f}",
            "Response included revenue amount and date range",
        ],
        expected_tool_calls=[calculate_revenue],
    )
    return case


def test_complex_scenario_1_category_inventory(goose_fixture: Goose):
    """Test: What Footwear products do we have in stock? (Complex - multi-tool)"""
    case = goose_fixture.case(
        query="What Footwear products do we have in stock?",
        expectations=[
            "Agent found products in Footwear category",
            "Agent checked inventory for the footwear products",
            "Response provided product names and their stock levels",
            "Agent used category search results to check inventory",
        ],
        expected_tool_calls=None,
    )
    return case


def test_complex_scenario_2_sale_and_inventory(goose_fixture: Goose):
    """Test: Sell 2 pairs of Hiking Boots to John and check remaining stock (Complex - multi-tool)"""
    # Capture counts before
    transactions_before = Transaction.objects.count()
    hiking_boots = Product.objects.get(name="Hiking Boots")
    inventory = ProductInventory.objects.filter(product=hiking_boots).first()
    assert inventory is not None, "Expected inventory record for Hiking Boots"
    stock_before = inventory.stock

    case = goose_fixture.case(
        query="Sell 2 pairs of Hiking Boots to John Doe and then tell me how many we have left",
        expectations=[
            "Agent created a sale transaction for 2 Hiking Boots to John Doe",
            "Agent then checked remaining inventory after the sale",
            "Response confirmed the sale was processed",
            "Response provided updated stock information",
            "Agent used sale creation output to inform inventory check",
        ],
        expected_tool_calls=[check_inventory, create_sale],
    )

    result: ValidationResult = asyncio.run(goose_fixture.run(case))
    assert result.success, result.reasoning

    # Check counts after
    transactions_after = Transaction.objects.count()
    assert (
        transactions_after == transactions_before + 1
    ), f"Expected 1 new transaction, got {transactions_after - transactions_before}"

    inventory_after = ProductInventory.objects.filter(product=hiking_boots).first()
    assert inventory_after is not None, "Expected inventory record after sale"
    assert inventory_after.stock == stock_before - 2, f"Expected stock {stock_before - 2}, got {inventory_after.stock}"

    return case


def test_complex_scenario_3_sales_history_and_analysis(goose_fixture: Goose):
    """Test: What were our sales in October 2025 and how much total revenue? (Complex - multi-tool)"""
    transactions = list(Transaction.objects.prefetch_related("items__product").all())
    total_revenue = (
        sum(item.price_usd * item.quantity for transaction in transactions for item in transaction.items.all())
        if transactions
        else 0
    )
    case = goose_fixture.case(
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
    return case
