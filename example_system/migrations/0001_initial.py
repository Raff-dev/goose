"""Initial database schema for the Goose example system."""

from __future__ import annotations

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    """Create core example system tables."""

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Product",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255, unique=True)),
                ("sku", models.CharField(max_length=64, unique=True)),
                ("category", models.CharField(max_length=128)),
                ("price_usd", models.FloatField()),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="Transaction",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("date", models.DateTimeField(default=django.utils.timezone.now)),
                ("buyer", models.JSONField(blank=True, null=True)),
            ],
            options={"ordering": ["-date"]},
        ),
        migrations.CreateModel(
            name="ProductInventory",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("stock", models.IntegerField(default=0)),
                (
                    "product",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="inventory",
                        to="example_system.product",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="TransactionItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("quantity", models.IntegerField()),
                ("price_usd", models.FloatField()),
                (
                    "product",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="line_items",
                        to="example_system.product",
                    ),
                ),
                (
                    "transaction",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="items",
                        to="example_system.transaction",
                    ),
                ),
            ],
        ),
    ]
