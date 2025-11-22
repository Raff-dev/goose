"""Command-line entrypoints for Goose.

This module exposes a single ``goose`` command implemented with Typer.

End-users interact with the installed console script::

    goose run path/to/tests
    goose run --list path/to/tests
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import typer
from typer import colors

from goose.testing import list_tests, run_tests

app = typer.Typer(help="Goose LLM testing CLI")


@app.command()
def run(
    path: str = typer.Argument(..., help="Directory containing Goose tests to discover"),
    list_only: bool = typer.Option(False, "--list", help="List discovered tests without executing them"),
) -> None:
    """Discover and run Goose tests under PATH.

    This mirrors the legacy ``goose run`` behavior and remains the
    default when the ``goose`` command is invoked without a subcommand.
    """

    target_path = Path(path)
    test_root = target_path.resolve()
    if test_root.is_file():
        test_root = test_root.parent

    for candidate in (test_root, test_root.parent):
        if str(candidate) not in sys.path:
            sys.path.insert(0, str(candidate))

    settings_module = os.environ.get("GOOSE_TEST_SETTINGS")
    if settings_module:
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", settings_module)

    if list_only:
        tests = list_tests(target_path)
        for definition in tests:
            print(definition.qualified_name)

        raise typer.Exit(code=0)

    results = run_tests(target_path)
    failures = _print_results(results)

    if failures:
        raise typer.Exit(code=1)

    raise typer.Exit(code=0)


def _print_results(results: list) -> int:
    """Print test results to stdout and return the number of failures.

    This helper extracts formatting and printing logic out of ``main`` to
    reduce the number of local variables in that function (keeps
    linting happy) while keeping output formatting centralized.
    """

    failures = 0
    for result in results:
        if result.passed:
            status_text = typer.style("PASS", fg=colors.GREEN)
        else:
            status_text = typer.style("FAIL", fg=colors.RED)

        duration_text = typer.style(f"{result.duration:.2f}s", fg=colors.CYAN)
        typer.echo(f"{status_text} {result.name} ({duration_text})")
        if result.error:
            typer.echo(typer.style(result.error, fg=colors.YELLOW if result.passed else colors.RED))
        if not result.passed:
            failures += 1

    typer.echo(
        f"{typer.style(str(len(results) - failures), fg=colors.GREEN)} passed, "
        f"{typer.style(str(failures), fg=colors.RED)} failed"
    )
    return failures
