"""Streamlit interface for inspecting and running Goose tests."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app import state  # pylint: disable=wrong-import-position
from app.components import (  # pylint: disable=wrong-import-position
    handle_run_all_tests,
    render_global_error,
    render_run_controls,
    render_suite_summary,
    render_test_details,
)
from app.services import test_execution  # pylint: disable=wrong-import-position


def main() -> None:
    """Entrypoint for the Goose test dashboard."""

    state.initialize_session_state()
    tests = test_execution.load_tests()

    run_clicked, only_failures = render_run_controls(tests)
    if run_clicked and tests:
        handle_run_all_tests()

    render_suite_summary(tests)
    render_global_error()
    render_test_details(tests, only_failures)


# Streamlit executes this module as a script.
main()
