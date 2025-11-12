"""High-level UI actions for the Goose dashboard."""

from __future__ import annotations

import streamlit as st  # type: ignore[import-not-found]

from app.services import test_execution


def handle_run_all_tests() -> None:
    """Execute the full test suite while showing progress feedback."""

    with st.spinner("Running all Goose tests. This can take a minute..."):
        test_execution.execute_run_all_tests()
