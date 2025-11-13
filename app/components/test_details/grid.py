"""Render the dashboard grid of discovered tests."""

from __future__ import annotations

from collections.abc import Sequence

import streamlit as st  # type: ignore[import-not-found]

from app import state
from app.components.common import render_status_badge
from app.components.test_details.shared import (
    STATUS_COLORS,
    duration_label,
    failure_summary,
    format_test_title,
    get_test_summary,
    status_badge_text,
    status_label,
)
from app.services import test_execution
from goose.testing import TestDefinition


def render_test_details(tests: Sequence[TestDefinition], only_failures: bool) -> None:
    """Render the dashboard grid of discovered tests."""

    st.subheader(f"Test Suite ({len(tests)})")

    if not tests:
        st.info("No tests discovered. Ensure your test modules are located under `example_tests/`.")
        return

    results_state = state.get_results_state()
    errors_state = state.get_errors_state()

    grid_definitions: list[TestDefinition] = []
    for definition in tests:
        qualified_name = definition.qualified_name
        result = results_state.get(qualified_name)
        test_error = errors_state.get(qualified_name)
        is_failure = (result is not None and not result.passed) or test_error is not None
        if only_failures and not is_failure:
            continue
        grid_definitions.append(definition)

    if not grid_definitions:
        st.info("No tests match the current filters.")
        return

    if only_failures:
        st.caption(f"Showing {len(grid_definitions)} failing test(s)")

    columns = st.columns(3)
    for index, definition in enumerate(grid_definitions):
        column = columns[index % 3]
        with column:
            _render_test_card(definition)
        if (index + 1) % 3 == 0 and (index + 1) < len(grid_definitions):
            columns = st.columns(3)


# pylint: disable=too-many-locals
def _render_test_card(definition: TestDefinition) -> None:
    qualified_name = definition.qualified_name
    results_state = state.get_results_state()
    errors_state = state.get_errors_state()

    result = results_state.get(qualified_name)
    test_error = errors_state.get(qualified_name)
    status_label_value = status_label(result, test_error)
    status_color = STATUS_COLORS[status_label_value]
    badge_text = status_badge_text(status_label_value, result, test_error)

    card = st.container(border=True)
    with card:
        header_col, badge_col = st.columns([0.7, 0.3])
        with header_col:
            st.markdown(f"**{format_test_title(definition.name)}**")
            st.caption(qualified_name)
        with badge_col:
            badge_placeholder = st.empty()
            render_status_badge(badge_text, status_color, container=badge_placeholder)

        summary = get_test_summary(definition)
        if summary:
            st.markdown(summary)

        failure_note = failure_summary(result, test_error)
        if failure_note:
            st.markdown(f"<span style='color:#dc2626'>{failure_note}</span>", unsafe_allow_html=True)

        duration_note = duration_label(result)
        if duration_note:
            st.caption(duration_note)

        action_cols = st.columns(2)
        with action_cols[0]:
            run_clicked = st.button(
                "Run",
                key=f"run-card-{qualified_name}",
                use_container_width=True,
                help="Execute only this test",
            )
        with action_cols[1]:
            detail_clicked = st.button(
                "View Details",
                key=f"detail-card-{qualified_name}",
                use_container_width=True,
            )

    if run_clicked:
        render_status_badge(
            "Running",
            STATUS_COLORS["Running"],
            container=badge_placeholder,
            show_spinner=True,
        )
        test_execution.execute_single_test(definition)
        st.rerun()

    if detail_clicked:
        state.set_selected_test(qualified_name)
        state.set_active_view("detail")
        st.rerun()
