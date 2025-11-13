"""Run-control UI components."""

from __future__ import annotations

from collections.abc import Sequence

import streamlit as st  # type: ignore[import-not-found]

from app import state
from goose.testing import TestDefinition
from goose.testing.types import TestResult


def render_run_controls(tests: Sequence[TestDefinition]) -> tuple[bool, bool]:
    """Render primary execution controls for the dashboard."""

    results_state = state.get_results_state()
    errors_state = state.get_errors_state()

    failing_count = sum(
        1
        for definition in tests
        if _is_failure(results_state.get(definition.qualified_name), errors_state.get(definition.qualified_name))
    )

    run_col, filter_col, extra_col = st.columns([2, 1, 1])
    with run_col:
        run_clicked = st.button(
            "Run All Tests",
            type="primary",
            disabled=not tests,
            use_container_width=True,
        )

    only_failures = state.get_only_failures_filter()
    toggle_label = (
        f"Showing failing only ({failing_count})" if only_failures else f"Show failing only ({failing_count})"
    )
    with filter_col:
        button_kwargs = {
            "key": "dashboard-failing-filter",
            "use_container_width": True,
            "help": "Limit the suite view to tests that previously failed or raised errors.",
        }
        if only_failures:
            button_kwargs["type"] = "primary"
        toggle_clicked = st.button(
            toggle_label,
            **button_kwargs,
        )

    with extra_col:
        view_errors = st.button(
            "View Errors",
            use_container_width=True,
            disabled=failing_count == 0,
            help="Jump to failing tests whenever errors are present.",
        )

    if toggle_clicked:
        only_failures = not only_failures

    if view_errors and failing_count:
        only_failures = True
        state.set_active_view("dashboard")

    state.set_only_failures_filter(only_failures)
    return run_clicked, only_failures


def _is_failure(result: TestResult | None, error: str | None) -> bool:
    if error:
        return True
    if result is None:
        return False
    return not result.passed
