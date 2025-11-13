"""Streamlit interface for inspecting and running Goose tests."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st  # type: ignore[import-not-found]

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app import state  # pylint: disable=wrong-import-position
from app.components import (  # pylint: disable=wrong-import-position
    handle_run_all_tests,
    render_global_error,
    render_run_controls,
    render_suite_summary,
    render_test_detail_view,
    render_test_details,
)
from app.services import test_execution  # pylint: disable=wrong-import-position


def main() -> None:
    """Entrypoint for the Goose test dashboard."""

    st.set_page_config(layout="wide", page_title="Goose Test Dashboard")

    state.initialize_session_state()
    tests = test_execution.load_tests()

    run_clicked, only_failures = render_run_controls(tests)
    if run_clicked and tests:
        handle_run_all_tests()

    render_suite_summary(tests)
    render_global_error()
    active_view = state.get_active_view()
    selected_name = state.get_selected_test()

    if active_view == "detail" and selected_name:
        definition = next((test for test in tests if test.qualified_name == selected_name), None)
        if definition is None:
            st.warning("Selected test no longer exists. Returning to dashboard view.")
            state.set_active_view("dashboard")
            state.set_selected_test(None)
            render_test_details(tests, only_failures)
            return

        result = state.get_results_state().get(selected_name)
        test_error = state.get_errors_state().get(selected_name)
        render_test_detail_view(definition, result, test_error)
    else:
        if selected_name is None and tests:
            state.set_selected_test(tests[0].qualified_name)
        render_test_details(tests, only_failures)


# Streamlit executes this module as a script.
main()
