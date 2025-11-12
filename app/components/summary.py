"""Summary widgets for the Goose dashboard."""

from __future__ import annotations

from collections.abc import Sequence

import streamlit as st  # type: ignore[import-not-found]

from app import state
from goose.testing import TestDefinition


def render_suite_summary(tests: Sequence[TestDefinition]) -> None:
    """Render metrics summarizing the current test suite."""

    st.subheader("Test Suite Overview")
    if not tests:
        st.info("No tests discovered. Ensure your test modules are located under `example_tests/`.")
        return

    results_state = state.get_results_state()
    total_tests = len(tests)
    executed = len(results_state)
    passed = sum(1 for item in results_state.values() if item.passed)
    failed = sum(1 for item in results_state.values() if not item.passed)

    summary_cols = st.columns(4)
    summary_cols[0].metric("Total tests", total_tests)
    summary_cols[1].metric("Executed", executed)
    summary_cols[2].metric("Passed", passed)
    summary_cols[3].metric("Failed", failed)

    last_run = state.get_last_run_time()
    if last_run is not None:
        st.caption(f"Last run: {last_run:%Y-%m-%d %H:%M:%S}")
