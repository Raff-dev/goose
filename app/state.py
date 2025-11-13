"""Session state helpers for the Goose Streamlit dashboard."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import streamlit as st  # type: ignore[import-not-found]

from goose.testing import TestResult

_SESSION_DEFAULTS: dict[str, Any] = {
    "test_results": {},
    "test_errors": {},
    "global_error": None,
    "last_run_time": None,
    "selected_test": None,
    "only_failures": False,
    "active_view": "dashboard",
    "show_global_error_details": False,
}


def initialize_session_state() -> None:
    """Ensure expected session state keys exist."""

    for key, default in _SESSION_DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = default


def get_results_state() -> dict[str, TestResult]:
    """Return the mutable mapping of stored test results."""

    return st.session_state["test_results"]


def get_errors_state() -> dict[str, str]:
    """Return the mutable mapping of unexpected execution errors."""

    return st.session_state["test_errors"]


def get_global_error() -> str | None:
    """Return any global runner error message."""

    return st.session_state.get("global_error")


def set_global_error(message: str | None) -> None:
    """Update the global error message."""

    st.session_state["global_error"] = message


def get_last_run_time() -> datetime | None:
    """Return the timestamp of the most recent test execution."""

    return st.session_state.get("last_run_time")


def set_last_run_time(timestamp: datetime | None) -> None:
    """Persist the timestamp of the most recent test execution."""

    st.session_state["last_run_time"] = timestamp


def get_selected_test() -> str | None:
    """Return the fully-qualified name of the currently selected test."""

    return st.session_state.get("selected_test")


def set_selected_test(qualified_name: str | None) -> None:
    """Persist the selected test name for the detail view."""

    st.session_state["selected_test"] = qualified_name


def get_only_failures_filter() -> bool:
    """Return whether the suite view should show only failing tests."""

    return bool(st.session_state.get("only_failures", False))


def set_only_failures_filter(value: bool) -> None:
    """Persist the current failing-only filter value."""

    st.session_state["only_failures"] = bool(value)


def get_active_view() -> str:
    """Return the current dashboard view identifier."""

    return st.session_state.get("active_view", "dashboard")


def set_active_view(view: str) -> None:
    """Persist the current dashboard view identifier."""

    st.session_state["active_view"] = view


def get_show_global_error_details() -> bool:
    """Return whether the global error panel should display full details."""

    return bool(st.session_state.get("show_global_error_details", False))


def set_show_global_error_details(value: bool) -> None:
    """Persist the expansion state for the global error panel."""

    st.session_state["show_global_error_details"] = bool(value)


def set_test_result(qualified_name: str, result: TestResult) -> None:
    """Store the latest result for a test."""

    get_results_state()[qualified_name] = result


def clear_test_error(qualified_name: str) -> None:
    """Remove a stored unexpected execution error for a test."""

    get_errors_state().pop(qualified_name, None)


def set_test_error(qualified_name: str, error: str) -> None:
    """Record an unexpected execution error for a test."""

    get_errors_state()[qualified_name] = error
