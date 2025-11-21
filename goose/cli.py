"""Command-line entrypoints for running Goose tests."""

from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Sequence
from pathlib import Path

from goose.testing import list_tests, run_tests

RESET = "\033[0m"
GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
CYAN = "\033[36m"


def _supports_color() -> bool:
    return sys.stdout.isatty() and os.environ.get("TERM") not in {"", "dumb"}


def _colorize(text: str, color: str) -> str:
    if not _supports_color():
        return text
    return f"{color}{text}{RESET}"


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point for the ``goose`` CLI command."""

    parser = argparse.ArgumentParser(description="Run Goose validation tests without pytest.")
    parser.add_argument(
        "path",
        nargs="?",
        default="example_tests",
        help="Directory containing Goose tests to discover",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List discovered tests without executing them",
    )
    args = parser.parse_args(argv)

    target_path = Path(args.path)
    test_root = target_path.resolve()
    if test_root.is_file():
        test_root = test_root.parent

    for candidate in (test_root, test_root.parent):
        if str(candidate) not in sys.path:
            sys.path.insert(0, str(candidate))

    settings_module = os.environ.get("GOOSE_TEST_SETTINGS")
    if settings_module:
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", settings_module)

    if args.list:
        tests = list_tests(target_path)
        for definition in tests:
            print(definition.qualified_name)
        return 0

    results = run_tests(target_path)
    failures = _print_results(results)

    return 1 if failures else 0


def _print_results(results: list) -> int:
    """Print test results to stdout and return the number of failures.

    This helper extracts formatting and printing logic out of ``main`` to
    reduce the number of local variables in that function (keeps
    linting happy) while keeping output formatting centralized.
    """

    failures = 0
    for result in results:
        status_text = _colorize("PASS" if result.passed else "FAIL", GREEN if result.passed else RED)
        duration_text = _colorize(f"{result.duration:.2f}s", CYAN)
        print(f"{status_text} {result.name} ({duration_text})")
        if result.error:
            print(_colorize(result.error, YELLOW if result.passed else RED))
        if not result.passed:
            failures += 1

    print(f"{_colorize(str(len(results) - failures), GREEN)} passed, " f"{_colorize(str(failures), RED)} failed")
    return failures
