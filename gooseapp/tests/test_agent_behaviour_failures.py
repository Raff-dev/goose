"""Intentional failure scenarios for agent behavior tests."""

from __future__ import annotations

from example_system.models import Product
from example_system.tools import (
    calculate_revenue,
    check_inventory,
    get_product_details,
    get_sales_history,
    trigger_system_fault,
)
from goose.testing import Goose


def test_failure_expectation_inventory_stock(goose: Goose) -> None:
    """Intentional failure: expectation should not match actual agent behaviour."""

    goose.case(
        query="What is the stock for Hiking Boots?",
        expectations=[
            "Agent reported that Hiking Boots are out of stock",
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
        expected_tool_calls=[check_inventory, get_sales_history],
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


def test_failure_tool_audit_extra_calls(goose: Goose) -> None:
    """Intentional failure: actual execution calls more tools than expected."""

    goose.case(
        query="Generate a detailed October 2025 sales summary with revenue totals.",
        expectations=[
            "Agent retrieved October 2025 sales history",
            "Agent provided revenue totals",
        ],
        expected_tool_calls=[get_sales_history],
    )


def test_failure_tool_runtime_trigger_system_fault(goose: Goose) -> None:
    """Intentional failure: tool raises an exception that propagates to the agent."""

    goose.case(
        query="Run the trigger system fault diagnostic and confirm the system is healthy.",
        expectations=[
            "Agent confirmed the system fault diagnostic succeeded",
        ],
        expected_tool_calls=[trigger_system_fault],
    )


def test_failure_error_before_goose(goose: Goose) -> None:
    """Intentional failure: raise an exception before any Goose case execution."""

    raise ValueError("Intentional failure: error before any Goose case execution")
