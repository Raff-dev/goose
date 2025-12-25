"""Django ORM backed LangChain tools for Goose Outfitters."""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any

from django.db import transaction as db_transaction
from django.db.models import Sum
from django.utils import timezone
from langchain_core.tools import tool

from example_system.models import Product, ProductInventory, Transaction, create_transaction


@tool
def get_product_details(product_name: str) -> dict[str, Any] | str:
    """Get detailed information about a specific product.

    Args:
        product_name: The name of the product to look up.

    Returns:
        Product details as a dictionary, or error message if not found.
    """
    product = (
        Product.objects.filter(name__iexact=product_name)
        .values(
            "name",
            "sku",
            "category",
            "price_usd",
        )
        .first()
    )

    if product is None:
        return f"Product '{product_name}' not found."

    return dict(product)


@tool
def check_inventory(product_name: str) -> dict[str, Any] | str:
    """Check inventory/stock levels for a product.

    Args:
        product_name: The name of the product to check.

    Returns:
        Inventory information as a dictionary, or error message.
    """
    product = Product.objects.filter(name__iexact=product_name).first()
    if product is None:
        return f"Product '{product_name}' not found."

    total_stock = ProductInventory.objects.filter(product=product).aggregate(total=Sum("stock"))
    return {
        "product_name": product_name,
        "total_stock": int(total_stock.get("total") or 0),
    }


@tool
def get_sales_history(start_date: str, end_date: str | None = None) -> list[dict[str, Any]] | str:
    """Get sales transaction history within a date range.

    Args:
        start_date: Start date in YYYY-MM-DD format.
        end_date: Optional end date in YYYY-MM-DD format. If None, uses current date.

    Returns:
        List of transaction summaries, or error message.
    """
    try:
        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date) if end_date else datetime.now()

        transactions = (
            Transaction.objects.filter(date__range=(start, end)).prefetch_related("items__product").order_by("date")
        )

        history: list[dict[str, Any]] = []
        for transaction in transactions:
            history.append(
                {
                    "date": transaction.date.isoformat(),
                    "buyer": transaction.buyer,
                    "total_usd": transaction.total_usd,
                    "total_quantity": transaction.total_quantity,
                    "items": [
                        {
                            "product_name": item.product.name,
                            "quantity": item.quantity,
                            "price_usd": item.price_usd,
                            "item_total_usd": item.total_usd,
                        }
                        for item in transaction.items.all()
                    ],
                }
            )

        return history

    except ValueError as e:
        return f"Invalid date format: {e}"


@tool
def calculate_revenue(start_date: str, end_date: str | None = None) -> dict[str, Any] | str:
    """Calculate total revenue from sales within a date range.

    Args:
        start_date: Start date in YYYY-MM-DD format.
        end_date: Optional end date in YYYY-MM-DD format. If None, uses current date.

    Returns:
        Revenue summary as a dictionary, or error message.
    """
    try:
        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date) if end_date else datetime.now()

        transactions = Transaction.objects.filter(date__range=(start, end)).prefetch_related("items")

        total_revenue = sum(item.total_usd for tx in transactions for item in tx.items.all())
        transaction_count = transactions.count()

        return {
            "start_date": start_date,
            "end_date": end_date or datetime.now().date().isoformat(),
            "total_revenue_usd": float(total_revenue),
            "transaction_count": transaction_count,
            "average_transaction_usd": float(total_revenue) / transaction_count if transaction_count else 0.0,
        }

    except ValueError as e:
        return f"Invalid date format: {e}"


@tool
def find_products_by_category(category: str) -> list[dict[str, Any]] | str:
    """Find all products in a specific category.

    Args:
        category: The product category to search for.

    Returns:
        List of products in the category, or message if none found.
    """
    products = Product.objects.filter(category__iexact=category).values("name", "sku", "price_usd").order_by("name")

    if not products:
        return f"No products found in category '{category}'."

    return [dict(product) for product in products]


@tool
def create_sale(products: dict[str, int], buyer_info: dict[str, Any]) -> dict[str, Any] | str:
    """Create a new sale transaction.

    Args:
        products: Dictionary mapping product names to quantities.
        buyer_info: Dictionary containing buyer information.

    Returns:
        Transaction summary as a dictionary, or error message.
    """
    if not products:
        return "No products specified for the sale."

    normalized: dict[str, int] = {name.strip(): quantity for name, quantity in products.items()}
    invalid = [name for name, qty in normalized.items() if qty <= 0]
    if invalid:
        return f"Invalid quantity for products: {', '.join(invalid)}."

    buyer_payload = buyer_info if isinstance(buyer_info, dict) else {}

    try:
        with db_transaction.atomic():
            product_map = {
                product.name.lower(): product for product in Product.objects.filter(name__in=list(normalized.keys()))
            }

            prepared: list[tuple[Product, int, ProductInventory]] = []
            for product_name, quantity in normalized.items():
                product = product_map.get(product_name.lower())
                if product is None:
                    raise ValueError(f"Product '{product_name}' not found.")

                inventory = ProductInventory.objects.select_for_update().filter(product=product).first()
                available = inventory.stock if inventory else 0
                if available < quantity:
                    raise ValueError(
                        f"Insufficient stock for '{product_name}'. Available: {available}, requested: {quantity}."
                    )

                if inventory is None:
                    raise ValueError(f"No inventory configured for '{product_name}'.")

                prepared.append((product, quantity, inventory))

            transaction = create_transaction(
                items=[
                    {"product": product, "quantity": quantity, "price_usd": product.price_usd}
                    for product, quantity, _ in prepared
                ],
                date=timezone.now(),
                buyer=buyer_payload,
            )

            for _, quantity, inventory in prepared:
                inventory.stock -= quantity
                inventory.save(update_fields=["stock"])

            return {
                "transaction_id": transaction.id,
                "date": transaction.date.isoformat(),
                "total_usd": transaction.total_usd,
                "total_quantity": transaction.total_quantity,
                "buyer": transaction.buyer,
                "items": [
                    {
                        "product_name": item.product.name,
                        "quantity": item.quantity,
                        "price_usd": item.price_usd,
                        "item_total_usd": item.total_usd,
                    }
                    for item in transaction.items.all()
                ],
            }
    except ValueError as error:  # pragma: no cover - defensive path
        return str(error)


@tool
def trigger_system_fault() -> str:
    """Always raise an error to simulate a failing diagnostic tool.

    Args:
        None

    Returns:
        This tool never returns successfully. It always raises a RuntimeError.
    """

    raise RuntimeError("System diagnostic failed: simulated infrastructure outage.")


@tool
def get_markdown_demo() -> str:
    """Returns a markdown-formatted string demonstrating various markdown features.

    This tool is useful for testing markdown rendering capabilities.

    Returns:
        A string containing various markdown elements.
    """
    return """# Goose Outfitters - Store Report

Welcome to the **Goose Outfitters** store report! This document showcases our *amazing* outdoor gear.

## Product Categories

We offer a wide range of products:

- **Backpacks** - For all your hiking needs
- **Tents** - From solo to family-sized
- **Footwear** - Boots, sandals, and more
  - Trail runners
  - Waterproof boots
  - Camp shoes

### Top Sellers

1. Trail Master Pro Backpack
2. Summit 4-Season Tent
3. Alpine Waterproof Boots

## Pricing Table

| Product | Category | Price | Stock |
|---------|----------|-------|-------|
| Trail Master Pro | Backpacks | $249.99 | 45 |
| Summit Tent | Tents | $399.99 | 12 |
| Alpine Boots | Footwear | $189.99 | 78 |

## Code Example

Here\'s how to use our API:

```python
from goose_outfitters import Client

client = Client(api_key="your-key")
products = client.get_products(category="backpacks")

for product in products:
    print(f"{product.name}: ${product.price}")
```

Inline code example: Use `get_product_details("Trail Master Pro")` to fetch details.

## Important Notes

> **Pro Tip:** Sign up for our newsletter to get 15% off your first order!
>
> We also offer free shipping on orders over $100.

---

### Links & References

Visit our [website](https://example.com) for more information.

![Goose Logo](https://example.com/logo.png)

### Contact

For support, email us at support@goose-outfitters.com or call ~~1-800-OLD-NUMBER~~ **1-800-GOOSE-GO**.

**Happy trails!** 🏔️
"""


@tool
async def check_weather_async(location: str) -> dict[str, Any]:
    """Check the current weather for a location (async demo tool).

    This is an async tool that simulates fetching weather data from an external API.

    Args:
        location: The location to check weather for (e.g., "Denver, CO").

    Returns:
        Weather information as a dictionary.
    """
    # Simulate async API call delay
    await asyncio.sleep(0.5)

    # Return mock weather data
    return {
        "location": location,
        "temperature_f": 42,
        "conditions": "Partly cloudy",
        "wind_mph": 8,
        "humidity_percent": 35,
        "forecast": "Great day for hiking!",
    }


# Export all tools for the agent
TOOLS = [
    get_product_details,
    check_inventory,
    get_sales_history,
    calculate_revenue,
    find_products_by_category,
    create_sale,
    trigger_system_fault,
    get_markdown_demo,
    check_weather_async,
]
