"""Configuration helpers for the Goose API server."""

from __future__ import annotations

from pathlib import Path

_STATE: dict = {
    "tests_root": Path.cwd(),
    "reload_targets": [],
}


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


def get_reload_targets() -> list[str]:
    """Return the list of module targets to reload before test discovery."""
    print(_STATE["reload_targets"])
    return _STATE["reload_targets"]


def set_reload_targets(targets: list[str]) -> None:
    """Set module targets to reload before test discovery.

    Args:
        targets: List of dotted module names to reload, e.g.
            ["example_system.agent", "example_system.tools"].
    """
    _STATE["reload_targets"] = list(targets)


__all__ = ["get_tests_root", "set_tests_root", "get_reload_targets", "set_reload_targets"]
