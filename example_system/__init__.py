"""Example system components for Goose Outfitters."""

from __future__ import annotations

import os
from types import ModuleType

try:
    import django
    from django.apps import apps
except ImportError:  # pragma: no cover - defensive path when Django missing
    django = None  # type: ignore[assignment]
    apps = None  # type: ignore[assignment]


def _configure_django() -> None:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "example_system.settings")
    if not isinstance(django, ModuleType) or apps is None:
        return

    if not apps.ready:
        django.setup()


_configure_django()
