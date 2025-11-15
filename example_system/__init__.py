"""Example system components for Goose Outfitters."""

from __future__ import annotations

import os

import django
from django.apps import apps


def _configure_django() -> None:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "example_system.settings")
    if not apps.ready:
        django.setup()


_configure_django()
