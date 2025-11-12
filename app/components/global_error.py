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

    st.error("Test run failed to complete.")
    render_scrollable_text("Error details", global_error, key="global-error-log")
