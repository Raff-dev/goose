"""Configuration helpers for the Goose API server."""

from __future__ import annotations

from pathlib import Path

_STATE: dict[str, Path] = {"tests_root": Path.cwd()}


def get_tests_root() -> Path:
    """Return the currently configured test discovery root."""

    return _STATE["tests_root"]


def set_tests_root(path: Path) -> None:
    """Update the test discovery root used by API endpoints."""

    _STATE["tests_root"] = path


__all__ = ["get_tests_root", "set_tests_root"]
