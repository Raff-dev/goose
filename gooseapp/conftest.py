"""Shared fixtures for Goose agent behaviour tests."""

from __future__ import annotations

from datetime import datetime

from django.utils import timezone

from example_system.agent import Agent
from example_system.models import Product, ProductInventory, Transaction, TransactionItem, create_transaction
from goose.testing import DjangoTestHooks, Goose, fixture


@fixture(autouse=True)
def setup_data() -> None:
    """Populate the database with sample data before each test."""
    TransactionItem.objects.all().delete()
    Transaction.objects.all().delete()
    ProductInventory.objects.all().delete()
    Product.objects.all().delete()

    hiking_boots = Product.objects.create(
        name="Hiking Boots",
        sku="BOOT001",
        category="Footwear",
        price_usd=150.0,
    )

    running_shoes = Product.objects.create(
        name="Running Shoes",
        sku="SHOE001",
        category="Footwear",
        price_usd=120.0,
    )

    backpack = Product.objects.create(
        name="Hiking Backpack",
        sku="PACK001",
        category="Gear",
        price_usd=200.0,
    )

    ProductInventory.objects.create(product=hiking_boots, stock=8)
    ProductInventory.objects.create(product=running_shoes, stock=5)
    ProductInventory.objects.create(product=backpack, stock=2)

    create_transaction(
        items=[
            {"product": hiking_boots, "quantity": 1, "price_usd": 150.0},
            {"product": backpack, "quantity": 1, "price_usd": 200.0},
        ],
        date=timezone.make_aware(datetime(2025, 10, 15, 0, 0)),
        buyer={"name": "Jane Smith", "email": "jane@example.com"},
    )


@fixture(name="goose")
def goose_fixture() -> Goose:
    """Provide a Goose testing instance for the agent.

    The GooseApp tools are available via gooseapp.app for reference,
    but the Goose instance uses the agent's built-in tools.
    """
    agent = Agent()
    return Goose(
        agent_query_func=agent.query,
        hooks=DjangoTestHooks(),
        validator_model="gpt-4o-mini",
    )
