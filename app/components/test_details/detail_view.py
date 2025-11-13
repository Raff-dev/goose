"""Detailed view rendering for a single test."""

from __future__ import annotations

import streamlit as st  # type: ignore[import-not-found]

from app import state
from app.components.common import render_scrollable_text, render_status_badge
from app.components.test_details.history import render_execution_history
from app.components.test_details.shared import (
    STATUS_COLORS,
    failure_summary,
    format_test_title,
    get_test_summary,
    status_badge_text,
    status_label,
)
from app.services import test_execution
from goose.testing import TestDefinition
from goose.testing.types import TestResult


def render_test_detail_view(
    definition: TestDefinition,
    result: TestResult | None,
    test_error: str | None,
) -> None:
    """Render the dedicated detail view for a single test."""

    qualified_name = definition.qualified_name
    status_label_value = status_label(result, test_error)
    status_color = STATUS_COLORS[status_label_value]
    badge_text = status_badge_text(status_label_value, result, test_error)

    nav_cols = st.columns([1.5, 6, 1])
    with nav_cols[0]:
        if st.button("← Back to Dashboard", key="detail-back-top", use_container_width=True):
            state.set_active_view("dashboard")
            st.rerun()
    with nav_cols[2]:
        st.caption("Dashboard")

    header = st.container(border=True)
    with header:
        title_col, badge_col = st.columns([4, 1])
        with title_col:
            st.subheader(format_test_title(definition.name))
            summary = get_test_summary(definition)
            if summary:
                st.write(summary)
            st.caption(f"Test ID: `{qualified_name}`")
        with badge_col:
            render_status_badge(badge_text, status_color)

    execution_count = len(result.executions) if result is not None else 0
    st.caption(f"{execution_count} execution(s) recorded")

    _render_test_status_section(qualified_name, result, test_error)

    failure_note = failure_summary(result, test_error)
    if failure_note and not test_error:
        st.markdown(
            f"<span style='color:#dc2626;font-weight:600'>Failure summary: {failure_note}</span>",
            unsafe_allow_html=True,
        )

    if test_error:
        _render_detail_actions(definition, show_back=True)
        return

    if result is None:
        st.info("Run this test to inspect agent executions and validator output.")
        _render_detail_actions(definition, show_back=True)
        return

    st.markdown("### Execution History")
    render_execution_history(qualified_name, result)
    _render_detail_actions(definition, show_back=True)


def _render_detail_actions(definition: TestDefinition, *, show_back: bool) -> None:
    action_cols = st.columns([1, 1, 3])
    run_col, back_col, _ = action_cols

    with run_col:
        if st.button("Run Test", use_container_width=True):
            with st.spinner("Running test..."):
                test_execution.execute_single_test(definition)
            state.set_selected_test(definition.qualified_name)
            state.set_active_view("detail")
            st.rerun()

    if show_back:
        with back_col:
            if st.button("Back to Dashboard", use_container_width=True):
                state.set_active_view("dashboard")
                st.rerun()


def _render_test_status_section(qualified_name: str, result: TestResult | None, test_error: str | None) -> None:
    status_container = st.container()
    with status_container:
        if test_error:
            st.error("Test execution raised an unexpected error.")
            render_scrollable_text(
                "Traceback",
                test_error,
                key=f"unexpected-error-{qualified_name}",
            )
            return

        if result is None:
            return

        if not result.passed:
            st.markdown(
                "<span style='color:#dc2626;font-weight:600'>Test failed. Review failure details below.</span>",
                unsafe_allow_html=True,
            )
