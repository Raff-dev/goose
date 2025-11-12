"""Django ORM models for the Goose example system."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import datetime
from typing import Any

from django.db import models
from django.db import transaction as db_transaction
from django.db.models import Manager
from django.utils import timezone


class Product(models.Model):
    """Product available for sale."""

    objects: Manager[Product] = models.Manager()
    name = models.CharField(max_length=255, unique=True)
    sku = models.CharField(max_length=64, unique=True)
    category = models.CharField(max_length=128)
    price_usd = models.FloatField()

    class Meta:
        """Model configuration for default ordering."""

        ordering = ["name"]

    def __str__(self) -> str:  # pragma: no cover - representation helper
        return f"{self.name} (${self.price_usd:.2f})"


class ProductInventory(models.Model):
    """Inventory level for a product in the warehouse."""

    objects: Manager[ProductInventory] = models.Manager()
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name="inventory")
    stock = models.IntegerField(default=0)


class Transaction(models.Model):
    """Sale transaction processed for Goose Outfitters."""

    objects: Manager[Transaction] = models.Manager()
    items: Manager[TransactionItem]
    date = models.DateTimeField(default=timezone.now)
    buyer = models.JSONField(blank=True, null=True)

    class Meta:
        """Model configuration for default ordering."""

        ordering = ["-date"]

    @property
    def total_usd(self) -> float:
        """Total price of all items in this transaction."""
        return sum(item.price_usd * item.quantity for item in self.items.all())

    @property
    def total_quantity(self) -> int:
        """Total item count within this transaction."""
        return sum(item.quantity for item in self.items.all())


class TransactionItem(models.Model):
    """Line item within a transaction."""

    objects: Manager[TransactionItem] = models.Manager()
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="line_items")
    quantity = models.IntegerField()
    price_usd = models.FloatField()

    @property
    def total_usd(self) -> float:
        """Total price contribution of this transaction line item."""
        return self.price_usd * self.quantity


def create_transaction(
    *,
    items: Iterable[TransactionItem | Mapping[str, Any]],
    date: datetime | None = None,
    buyer: Mapping[str, Any] | None = None,
) -> Transaction:
    """Create a transaction and persist associated line items in the database."""

    date_value = date or timezone.now()
    buyer_payload: dict[str, Any] | None = dict(buyer) if buyer is not None else None

    with db_transaction.atomic():
        transaction = Transaction.objects.create(
            date=date_value,
            buyer=buyer_payload,
        )

        for item in items:
            if isinstance(item, TransactionItem):
                TransactionItem.objects.create(
                    transaction=transaction,
                    product=item.product,
                    quantity=item.quantity,
                    price_usd=item.price_usd,
                )
            else:
                TransactionItem.objects.create(
                    transaction=transaction,
                    product=item["product"],
                    quantity=item["quantity"],
                    price_usd=item["price_usd"],
                )

    return transaction
