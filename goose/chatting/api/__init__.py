"""Chatting API module."""

from __future__ import annotations

# pylint: disable=import-outside-toplevel


def get_router():
    """Get the chatting router (lazy import to avoid circular imports)."""
    from goose.chatting.api.router import router

    return router


__all__ = ["get_router"]
