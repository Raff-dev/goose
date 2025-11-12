"""Run-control UI components."""

from __future__ import annotations

from collections.abc import Sequence

import streamlit as st  # type: ignore[import-not-found]

from goose.testing import TestDefinition


def render_run_controls(tests: Sequence[TestDefinition]) -> tuple[bool, bool]:
    """Render the run-all button and failure filter checkbox."""

    control_col, filter_col = st.columns([2, 1])
    with control_col:
        run_clicked = st.button("Run All Tests", type="primary", disabled=not tests)
    with filter_col:
        only_failures = st.checkbox("Show only failing tests", value=False)
    return run_clicked, only_failures
