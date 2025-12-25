"""Shared fixtures for Goose agent behaviour tests."""

from __future__ import annotations

from datetime import datetime

from django.utils import timezone
from langchain_core.messages import BaseMessage, HumanMessage

from example_system.agent import agent
from example_system.models import Product, ProductInventory, Transaction, TransactionItem, create_transaction
from goose.testing import DjangoTestHooks, Goose, fixture
from goose.testing.exceptions import AgentQueryError
from goose.testing.models.messages import AgentResponse, Message


def query(question: str, history: list[BaseMessage] | None = None) -> AgentResponse:
    """Query the agent with a question using streaming to capture partial responses.

    Args:
        question: The question to ask the agent.
        history: Optional list of previous conversation messages.

    Returns:
        The agent's response payload.

    Raises:
        AgentQueryError: If the agent fails, with partial_response attached if available.
    """
    input_messages = (history or []) + [HumanMessage(content=question)]
    collected_messages: list[Message] = [Message.from_langchain_message(m) for m in input_messages]
    last_state_messages: list[BaseMessage] = []

    try:
        # Use stream_mode="values" to get complete state after each step
        for state in agent.stream({"messages": input_messages}, stream_mode="values"):
            last_state_messages = state.get("messages", [])

        # Convert final state messages to our Message format
        collected_messages = [Message.from_langchain_message(m) for m in last_state_messages]
        return AgentResponse(messages=collected_messages)
    except Exception as exc:
        # If we captured any state before failure, use it
        if last_state_messages:
            collected_messages = [Message.from_langchain_message(m) for m in last_state_messages]
        partial = AgentResponse(messages=collected_messages) if collected_messages else None
        raise AgentQueryError(str(exc), partial_response=partial) from exc


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
    return Goose(
        agent_query_func=query,
        hooks=DjangoTestHooks(),
        validator_model="gpt-4o-mini",
    )
