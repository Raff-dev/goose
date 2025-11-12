"""Test detail cards for the Goose dashboard."""

from __future__ import annotations

import json
from collections.abc import Sequence

import streamlit as st  # type: ignore[import-not-found]

from app import state
from app.components.common import render_scrollable_text, render_status_badge
from app.services import test_execution
from goose.agent_validator import ValidationResult
from goose.testing import TestDefinition
from goose.testing.types import ExecutionRecord, TestResult

_STATUS_COLORS: dict[str, str] = {
    "Error": "#dc2626",
    "Not run": "#64748b",
    "Passed": "#16a34a",
    "Failed": "#dc2626",
}


# pylint: disable=too-many-locals
def render_test_details(tests: Sequence[TestDefinition], only_failures: bool) -> None:
    """Render the list of test cards."""

    if not tests:
        return

    st.subheader("Test Details")
    results_state = state.get_results_state()
    errors_state = state.get_errors_state()

    for definition in tests:
        qualified_name = definition.qualified_name
        result = results_state.get(qualified_name)
        test_error = errors_state.get(qualified_name)
        is_failure = (result is not None and not result.passed) or test_error is not None

        if only_failures and not is_failure:
            continue

        status_label = _status_label(result, test_error)
        status_color = _STATUS_COLORS[status_label]

        card = st.container(border=True)
        with card:
            name_col, status_col, run_col = st.columns([6, 2, 1])
            with name_col:
                st.markdown(f"**{qualified_name}**")
            with status_col:
                render_status_badge(status_label, status_color)
            with run_col:
                run_single = st.button(
                    "Run",
                    key=f"run-single-{qualified_name}",
                    icon="▶️",
                    use_container_width=True,
                    help="Run this test",
                )

            if run_single:
                _run_single_test(definition)
                result = results_state.get(qualified_name)
                test_error = errors_state.get(qualified_name)
                status_label = _status_label(result, test_error)
                status_color = _STATUS_COLORS[status_label]
                with status_col:
                    render_status_badge(status_label, status_color)

            _render_execution_history(qualified_name, result)
            _render_test_status_section(qualified_name, result, test_error)


def _status_label(result: TestResult | None, test_error: str | None) -> str:
    if test_error:
        return "Error"
    if result is None:
        return "Not run"
    return "Passed" if result.passed else "Failed"


def _run_single_test(definition: TestDefinition) -> None:
    with st.spinner(f"Running {definition.qualified_name}..."):
        test_execution.execute_single_test(definition)


def _render_test_status_section(qualified_name: str, result: TestResult | None, test_error: str | None) -> None:
    status_container = st.container()
    with status_container:
        if test_error:
            st.error("Test execution raised an unexpected error.")
            render_scrollable_text(
                "Traceback",
                test_error,
                key=f"unexpected-error-{qualified_name}",
            )
            return

        if result is None:
            st.info("Test has not been executed yet.")
            return

        if result.passed:
            st.success(f"Passed in {result.duration:.2f}s")
        else:
            st.error(f"Failed in {result.duration:.2f}s")
            if result.error:
                with st.expander("Failure details", expanded=False):
                    render_scrollable_text(
                        "Failure details",
                        result.error,
                        key=f"failure-details-{qualified_name}",
                    )


def _render_execution_history(qualified_name: str, result: TestResult | None) -> None:
    if result is None or not result.executions:
        return

    with st.expander("Agent executions", expanded=False):
        for exec_index, execution in enumerate(result.executions, start=1):
            run_container = st.container(border=True)
            with run_container:
                st.markdown(f"**Run {exec_index}** — `{execution.query}`")

                if execution.expectations:
                    _render_expectations(execution.expectations, execution.validation)

                if execution.expected_tool_calls:
                    expected_tools = ", ".join(f"`{name}`" for name in execution.expected_tool_calls)
                    st.markdown(f"Expected tool calls: {expected_tools}")

                if execution.validation and execution.validation.reasoning:
                    render_scrollable_text(
                        "Validator reasoning",
                        execution.validation.reasoning,
                        key=f"validation-reasoning-{qualified_name}-{exec_index}",
                        min_lines=4,
                    )

                if execution.error:
                    render_scrollable_text(
                        "Execution error",
                        execution.error,
                        key=f"execution-error-{qualified_name}-{exec_index}",
                    )

                _render_messages(qualified_name, exec_index, execution)


def _render_expectations(expectations: Sequence[str], validation: ValidationResult | None) -> None:
    if validation is None:
        st.markdown("**Expectations**")
        for index, expectation in enumerate(expectations, start=1):
            st.markdown(f"• **{index}.** {expectation}")
        return

    unmet_numbers = set(getattr(validation, "unmet_expectation_numbers", []))
    st.markdown("**Expectations**")
    for index, expectation in enumerate(expectations, start=1):
        icon = "❌" if index in unmet_numbers else "✅"
        st.markdown(f"{icon} **{index}.** {expectation}")


def _render_messages(qualified_name: str, exec_index: int, execution: ExecutionRecord) -> None:
    response = execution.response
    if response is None or not response.messages:
        return

    st.markdown("**Messages**")
    for msg_index, message in enumerate(response.messages, start=1):
        prefix = message.type.capitalize()
        if message.type == "human":
            st.markdown(f"{prefix}: {message.content}")
        elif message.type == "ai":
            st.markdown(f"{prefix} response")
            if message.content:
                render_scrollable_text(
                    "AI content",
                    message.content,
                    key=f"ai-content-{qualified_name}-{exec_index}-{msg_index}",
                    min_lines=4,
                )
            if message.tool_calls:
                st.markdown("Tool calls:")
                for call_index, call in enumerate(message.tool_calls, start=1):
                    st.markdown(f"- `{call.name}`")
                    if call.args:
                        formatted_args = json.dumps(call.args, indent=2, sort_keys=True)
                        render_scrollable_text(
                            "Arguments",
                            formatted_args,
                            key=(f"tool-args-{qualified_name}-{exec_index}-" f"{msg_index}-{call_index}"),
                            min_lines=4,
                        )
        elif message.type == "tool":
            label = f"Tool `{message.tool_name or 'unknown'}` response"
            render_scrollable_text(
                label,
                message.content,
                key=f"tool-response-{qualified_name}-{exec_index}-{msg_index}",
                min_lines=4,
            )
