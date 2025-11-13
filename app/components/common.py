"""Shared UI helpers for the Goose Streamlit dashboard."""

from __future__ import annotations

import streamlit as st  # type: ignore[import-not-found]
from streamlit.delta_generator import DeltaGenerator  # type: ignore[import-not-found]

_BADGE_BASE_STYLE = "".join(
    [
        "display:inline-flex;align-items:center;gap:0.4rem;padding:0.15rem 0.55rem;",
        "border-radius:999px;font-weight:600;",
    ]
)

_SPINNER_STYLE = """
<style>
@keyframes goose-badge-spin {
    to { transform: rotate(360deg); }
}
.goose-badge-spinner {
    width: 0.9rem;
    height: 0.9rem;
    border-radius: 50%;
    border: 2px solid currentColor;
    border-bottom-color: transparent;
    border-left-color: transparent;
    display: inline-block;
    animation: goose-badge-spin 0.6s linear infinite;
}
</style>
"""


def render_scrollable_text(label: str, content: str, *, key: str, min_lines: int = 6, max_lines: int = 32) -> None:
    """Render multiline text that scrolls vertically without horizontal overflow."""

    line_count = max(1, len(content.splitlines()))
    height = min(max(line_count, min_lines), max_lines) * 18
    st.text_area(label, content, height=height, disabled=True, key=key)


def render_status_badge(
    label: str,
    color: str,
    *,
    container: DeltaGenerator | None = None,
    show_spinner: bool = False,
) -> None:
    """Display a pill-style status badge."""

    if show_spinner and not st.session_state.get("_goose_badge_spinner_css"):
        st.session_state["_goose_badge_spinner_css"] = True
        st.markdown(_SPINNER_STYLE, unsafe_allow_html=True)

    target = container or st
    spinner_html = ""
    if show_spinner:
        spinner_html = f"<span class='goose-badge-spinner' style='color:{color}'></span>"

    target.markdown(
        (
            f"<span style='{_BADGE_BASE_STYLE}background-color:{color}20;color:{color};'>"
            f"{spinner_html}<span>{label}</span></span>"
        ),
        unsafe_allow_html=True,
    )
