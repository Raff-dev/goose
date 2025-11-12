"""Command-line entrypoints for running Goose tests."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from goose.testing import list_tests, run_tests


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point for the ``goose-tests`` CLI command."""

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

    if args.list:
        tests = list_tests(target_path)
        for definition in tests:
            print(definition.qualified_name)
        return 0

    results = run_tests(target_path)
    failures = 0

    for result in results:
        status = "PASS" if result.passed else "FAIL"
        print(f"{status} {result.name} ({result.duration:.2f}s)")
        if result.error:
            print(result.error)
        if not result.passed:
            failures += 1

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
