"""Configuration helpers for the Goose API server."""

from __future__ import annotations

from pathlib import Path

_STATE: dict[str, Path] = {"tests_root": Path.cwd()}


def get_tests_root() -> Path:
    """Return the currently configured test discovery root."""

    return _STATE["tests_root"]


def set_tests_root(path: Path) -> None:
    """Update the test discovery root used by API endpoints."""
    if path.is_file():
        raise ValueError("Tests root must be a directory, not a file")

    if not path.exists():
        raise ValueError(f"Tests root '{path}' does not exist")

    if not path.is_dir():
        raise ValueError(f"Tests root '{path}' is not a directory")

    _STATE["tests_root"] = path.resolve()


__all__ = ["get_tests_root", "set_tests_root"]
