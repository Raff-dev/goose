"""Summary widgets for the Goose dashboard."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from html import escape

import streamlit as st  # type: ignore[import-not-found]

from app import state
from goose.testing import TestDefinition


@dataclass(frozen=True)
class SuiteStats:  # pylint: disable=too-many-instance-attributes
    """Lightweight container for aggregated suite statistics.

    Attributes are intentionally simple and positional because this is a
    small value object used only to communicate metrics to the render code.
    """

    total_tests: int
    executed: int
    passed: int
    failed: int
    execution_rate: str
    last_run: datetime | None
    total_duration: float
    overall_status: str


def render_suite_summary(tests: Sequence[TestDefinition]) -> None:
    """Render metrics summarizing the current test suite."""

    st.subheader("Test Suite Overview")
    if not tests:
        st.info("No tests discovered. Ensure your test modules are located under `example_tests/`.")
        return

    stats = _collect_suite_stats(tests)

    metric_data = [
        ("Total Tests", stats.total_tests, None),
        ("Executed", stats.executed, stats.execution_rate),
        ("Passed", stats.passed, None),
        ("Failed", stats.failed, None),
    ]

    summary_cols = st.columns(4)
    for column, (label, value, extra) in zip(summary_cols, metric_data, strict=False):
        card = column.container(border=True)
        with card:
            card.markdown(f"**{label}**")
            card.markdown(f"<span style='font-size:2rem;font-weight:600'>{value}</span>", unsafe_allow_html=True)
            extra_display = escape(extra) if extra is not None else "&nbsp;"
            card.markdown(
                f"<div style='min-height:1.25rem;color:#64748b;font-size:0.85rem'>{extra_display}</div>",
                unsafe_allow_html=True,
            )

    formatted_duration = _format_duration(stats.total_duration)

    info_card = st.container(border=True)
    with info_card:
        info_cols = st.columns([2, 1, 1])
        with info_cols[0]:
            st.markdown("**Last Run Time**")
            if stats.last_run is not None:
                st.markdown(f"{stats.last_run:%b %d, %Y, %I:%M %p}")
            else:
                st.markdown("—")
        with info_cols[1]:
            st.markdown("**Duration**")
            st.markdown(formatted_duration)
        with info_cols[2]:
            st.markdown("**Overall Status**")
            status_color = "#16a34a" if stats.overall_status == "Passed" else "#dc2626"
            st.markdown(
                f"<span style='color:{status_color};font-weight:600'>{stats.overall_status}</span>",
                unsafe_allow_html=True,
            )


def _collect_suite_stats(tests: Sequence[TestDefinition]) -> SuiteStats:
    results_state = state.get_results_state()
    errors_state = state.get_errors_state()

    total_tests = len(tests)
    executed_keys = set(results_state.keys()) | set(errors_state.keys())
    executed = len(executed_keys)
    passed = sum(1 for item in results_state.values() if item.passed)
    failed_from_results = sum(1 for item in results_state.values() if not item.passed)
    failed = failed_from_results + len(errors_state)
    execution_rate = f"{executed / total_tests:.0%}" if total_tests else "0%"
    last_run = state.get_last_run_time()
    total_duration = sum(result.duration for result in results_state.values())
    overall_status = "Passed" if failed == 0 else "Failed"

    return SuiteStats(
        total_tests=total_tests,
        executed=executed,
        passed=passed,
        failed=failed,
        execution_rate=execution_rate,
        last_run=last_run,
        total_duration=total_duration,
        overall_status=overall_status,
    )


def _format_duration(duration_seconds: float) -> str:
    if duration_seconds <= 0:
        return "—"

    minutes, seconds = divmod(duration_seconds, 60)
    if minutes >= 1:
        return f"{int(minutes)}m {int(seconds):02d}s"
    return f"{int(seconds)}s"
