"""Execution history rendering for test detail view."""

from __future__ import annotations

import json

import streamlit as st  # type: ignore[import-not-found]
from streamlit.delta_generator import DeltaGenerator  # type: ignore[import-not-found]

from app.components.common import render_scrollable_text, render_status_badge
from app.components.test_details.shared import STATUS_COLORS, failure_summary
from goose.agent_validator import ValidationResult
from goose.testing.types import ExecutionRecord, TestResult


def render_execution_history(qualified_name: str, result: TestResult | None) -> None:
    """Render execution history entries for the selected test."""
    if result is None or not result.executions:
        return

    total_runs = len(result.executions)

    for exec_index, execution in enumerate(reversed(result.executions), start=1):
        run_number = total_runs - exec_index + 1
        run_container = st.container(border=True)
        with run_container:
            header_cols = st.columns([0.7, 0.3])
            with header_cols[0]:
                st.markdown(f"**Run {run_number}** — `{execution.query}`")
                if exec_index == 1:
                    st.caption("Latest execution")
            with header_cols[1]:
                status_label_value = _execution_status_label(execution)
                render_status_badge(status_label_value, STATUS_COLORS[status_label_value])

            expectations_tab, messages_tab = st.tabs(["Expectations", "Messages"])

            with expectations_tab:
                if execution.expectations:
                    _render_expectations(
                        execution.expectations,
                        execution.validation,
                        container=expectations_tab,
                    )
                else:
                    expectations_tab.markdown("No expectations defined for this run.")

                if execution.expected_tool_calls:
                    expected_tools = ", ".join(f"`{name}`" for name in execution.expected_tool_calls)
                    expectations_tab.markdown(f"Expected tool calls: {expected_tools}")

                if execution.validation and execution.validation.reasoning:
                    render_scrollable_text(
                        "Validator reasoning",
                        execution.validation.reasoning,
                        key=f"validation-reasoning-{qualified_name}-{exec_index}",
                        min_lines=4,
                    )

                failure_rendered = False
                if execution.error:
                    render_scrollable_text(
                        "Execution error",
                        execution.error,
                        key=f"execution-error-{qualified_name}-{exec_index}",
                    )
                    failure_rendered = True

                if not execution.error and not result.passed and result.error:
                    render_scrollable_text(
                        "Failure details",
                        result.error,
                        key=f"failure-details-{qualified_name}-{exec_index}",
                    )
                    failure_rendered = True

                if not failure_rendered:
                    fallback = failure_summary(result, None)
                    if fallback:
                        expectations_tab.markdown(fallback)

            with messages_tab:
                _render_messages(execution, container=messages_tab)


def _render_expectations(
    expectations: list[str],
    validation: ValidationResult | None,
    *,
    container: DeltaGenerator,
) -> None:
    """Render the expectations tab for a single execution."""
    if validation is None:
        container.markdown("**Expectations**")
        for expectation in expectations:
            container.markdown(f"• {expectation}")
        return

    unmet_numbers = set(getattr(validation, "unmet_expectation_numbers", []))
    container.markdown("**Expectations**")
    for index, expectation in enumerate(expectations, start=1):
        icon = "❌" if index in unmet_numbers else "✅"
        container.markdown(f"{icon} {expectation}")


def _render_messages(
    execution: ExecutionRecord,
    *,
    container: DeltaGenerator,
) -> None:
    """Render the conversational messages for an execution."""
    response = execution.response
    if response is None or not response.messages:
        container.markdown("No messages recorded for this run.")
        return

    for message in response.messages:
        role = _chat_role_for_message(message.type)
        chat = container.chat_message(role)
        if message.type == "human":
            chat.markdown(message.content or "_No user content_")
        elif message.type == "ai":
            if message.content:
                chat.markdown(message.content)
            else:
                chat.markdown("_Agent responded without text content._")

            if message.tool_calls:
                chat.markdown("**Tool calls**")
                for call_index, call in enumerate(message.tool_calls, start=1):
                    chat.markdown(f"{call_index}. `{call.name}`")
                    if call.args:
                        formatted_args = json.dumps(call.args, indent=2, sort_keys=True)
                        chat.code(formatted_args, language="json")
        elif message.type == "tool":
            title = f"Tool `{message.tool_name or 'unknown'}` response"
            chat.markdown(f"**{title}**")
            if message.content:
                _render_tool_output(chat, message.content)
            else:
                chat.markdown("_Tool returned no content._")


def _chat_role_for_message(message_type: str) -> str:
    """Map stored message type to the Streamlit chat role."""
    if message_type == "human":
        return "user"
    if message_type == "ai":
        return "assistant"
    return "tool"


def _render_tool_output(chat: DeltaGenerator, content: str) -> None:
    """Render tool output content within a chat message."""
    normalized = content.strip()
    if not normalized:
        chat.markdown("_Tool returned no content._")
        return

    try:
        parsed = json.loads(normalized)
    except json.JSONDecodeError:
        chat.markdown(content)
        return

    formatted = json.dumps(parsed, indent=2, sort_keys=True)
    chat.code(formatted, language="json")


def _execution_status_label(execution: ExecutionRecord) -> str:
    """Derive the status label to display for an execution."""
    if execution.error:
        return "Error"
    validation = execution.validation
    if validation is None:
        return "Passed"
    return "Passed" if getattr(validation, "success", True) else "Failed"
