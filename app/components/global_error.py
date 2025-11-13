"""Global error banner for the Goose dashboard."""

from __future__ import annotations

import streamlit as st  # type: ignore[import-not-found]

from app import state
from app.components.common import render_scrollable_text


def render_global_error() -> None:
    """Display the global runner error, if any."""

    global_error = state.get_global_error()
    if not global_error:
        return

    details_open = state.get_show_global_error_details()
    error_lines = [line for line in global_error.strip().splitlines() if line.strip()]
    error_title = error_lines[0] if error_lines else "Unexpected test runner error"

    card = st.container(border=True)
    with card:
        st.markdown("### Critical Suite Failure")
        st.markdown(f"**{error_title}**")
        st.caption("Test orchestrator failed to complete the requested operation.")

        action_cols = st.columns(3)
        with action_cols[0]:
            toggle_label = "Hide Details" if details_open else "Show Details"
            if st.button(toggle_label, key="global-error-toggle", use_container_width=True):
                state.set_show_global_error_details(not details_open)
                st.rerun()

        with action_cols[1]:
            if st.button("Dismiss", key="global-error-dismiss", use_container_width=True):
                state.set_global_error(None)
                state.set_show_global_error_details(False)
                st.rerun()

        with action_cols[2]:
            if st.button("View Full Log", key="global-error-view-log", use_container_width=True):
                state.set_show_global_error_details(True)
                st.rerun()

        total_errors = len(state.get_errors_state())
        if total_errors:
            st.caption(f"{total_errors} total error(s) recorded across tests")

        if details_open:
            render_scrollable_text("Error details", global_error, key="global-error-log")
