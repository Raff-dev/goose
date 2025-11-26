"""Import helpers shared across Goose CLI and discovery modules."""

from __future__ import annotations

import sys
from pathlib import Path


def ensure_test_import_paths(target_path: Path) -> Path:
    """Ensure *target_path* and its parent are on ``sys.path``.

    The function resolves ``target_path`` to a directory that contains
    Goose tests. If a file is provided, its parent directory is used.
    Both the resolved directory and its parent folder are prepended to
    ``sys.path`` (if not already present) so locally defined test
    modules, fixtures, and helpers can be imported no matter where the
    CLI/API is executed from. The resolved directory is returned for
    callers that need to perform additional path calculations.
    """

    test_root = target_path.resolve()
    if test_root.is_file():
        test_root = test_root.parent

    for candidate in (test_root, test_root.parent):
        candidate_path = str(candidate)
        if candidate_path not in sys.path:
            sys.path.insert(0, candidate_path)

    return test_root


__all__ = ["ensure_test_import_paths"]
