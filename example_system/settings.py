"""Minimal Django settings for the example system."""

from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "unsafe-example-secret")

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "example_system",
]

DATABASES = {
    "default": {
        "ENGINE": os.getenv("GOOSE_DB_ENGINE", "django.db.backends.postgresql"),
        "NAME": os.getenv("GOOSE_DB_NAME", "goose"),
        "USER": os.getenv("GOOSE_DB_USER", "goose"),
        "PASSWORD": os.getenv("GOOSE_DB_PASSWORD", "goose"),
        "HOST": os.getenv("GOOSE_DB_HOST", "localhost"),
        "PORT": os.getenv("GOOSE_DB_PORT", "5432"),
    }
}

USE_TZ = True
TIME_ZONE = os.getenv("GOOSE_TIME_ZONE", "UTC")

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
