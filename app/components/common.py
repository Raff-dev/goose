"""Shared UI helpers for the Goose Streamlit dashboard."""

from __future__ import annotations

import streamlit as st  # type: ignore[import-not-found]


def render_scrollable_text(label: str, content: str, *, key: str, min_lines: int = 6, max_lines: int = 32) -> None:
    """Render multiline text that scrolls vertically without horizontal overflow."""

    line_count = max(1, len(content.splitlines()))
    height = min(max(line_count, min_lines), max_lines) * 18
    st.text_area(label, content, height=height, disabled=True, key=key)


def render_status_badge(label: str, color: str) -> None:
    """Display a pill-style status badge."""

    st.markdown(
        f"<span style='display:inline-block;padding:0.15rem 0.55rem;border-radius:999px;"
        f"background-color:{color}20;color:{color};font-weight:600;'> {label} </span>",
        unsafe_allow_html=True,
    )
