# Goose Streamlit Dashboard PRD

## Overview
The Goose Streamlit dashboard is a packaged user interface for inspecting, running, and troubleshooting Goose LLM tests. It ships alongside the Goose library so teams can install `goose-llm[ui]` and launch an interactive test console (`goose-dashboard`). The dashboard surfaces suite-wide health, individual test status, execution history, and run controls that trigger Goose’s testing engine.

## Objectives
- Enable non-Python specialists (QA, product) to trigger Goose test suites and review results without navigating code.
- Provide fast visibility into suite status, failures, and underlying validator reasoning.
- Offer an opinionated test detail layout aligned with Goose data models while remaining extensible for future filters and reporting.
- Maintain parity between library state and UI by reusing Goose’s execution services and session helpers.

## Target Users & Use Cases
- **QA Engineer**: Run the full suite before a release, monitor pass/fail counts, inspect failures for validator reasoning, and re-run individual tests.
- **Developer**: Debug a failing agent test, review tool call mismatches, browse chat transcripts, and validate fixes via “Run Test”.
- **Product/Support**: Glance at suite health, understand failure summaries, and share errors or logs with the engineering team.

## Core User Flows
1. **Launch Dashboard**
   - User installs goose-llm with the UI extra.
   - Runs `goose-dashboard`; Streamlit boots `goose.ui.app.main`.
   - Session state initializes with result/error storage and default view (dashboard).

2. **Execute Entire Suite**
   - User clicks “Run All Tests”.
   - UI spinner appears while `goose.ui.services.test_execution.execute_run_all_tests()` runs Goose’s test runner.
   - On completion the summary metrics, grid cards, and execution histories update, and any global errors are displayed.

3. **Filter to Failing Tests**
   - User toggles “Show failing only”; session state stores the flag.
   - Grid re-renders showing only tests with failures or execution errors.

4. **Dive into Test Details**
   - From a grid card, the user clicks “View Details”.
   - Detail view loads with header badge, summary, failure callout, and execution history cards.
   - Tabs provide expectations/outcomes vs. chat transcript, including tool call JSON.

5. **Re-run a Single Test**
   - User presses “Run Test” in detail view or “Run” on a card.
   - UI shows a spinner, state records the latest result/error, and components update accordingly.

6. **Handle Runner Errors**
   - Any unexpected exception surfaces as a global banner with actions to show/hide details and dismiss.
   - Scrollable traceback allows copying logs for debugging.

## Information Architecture
- **Summary Row**: Four metric cards (Total, Executed, Passed, Failed) plus an info card (Last Run Time, Duration, Overall Status).
- **Run Controls**: Buttons for Run All, failing-only toggle, and View Errors shortcut.
- **Global Error Banner**: Conditional card showing suite-level failures, with detail toggles.
- **Content Panel**:
  - **Dashboard View**: Three-column grid of test cards with status badges, summary copy, failure tags, and action buttons.
  - **Detail View**: Header with back navigation, metadata, failure summary, and execution history section containing run-by-run cards with Expectations/Messages tabs.

## Data Model & State
- Session keys: `test_results`, `test_errors`, `selected_test`, `only_failures`, `active_view`, `global_error`, `show_global_error_details`, `last_run_time`.
- `goose.ui.services.test_execution` consumes Goose’s core runner (`run_tests`, `run_single_test`) and writes results back to session state.
- Components derive status colors, failure summaries, and duration labels via shared helpers (`goose.ui.components.test_details.shared`).

## Feature Requirements
- Display suite metrics with consistent card heights.
- Render grid cards with conditional failure summary chips (tool mismatch, assertion failure, expectations unmet, unexpected error).
- Allow toggling failing-only filter and persist selection across reruns.
- Support navigation between dashboard/detail views without losing selection.
- For each execution run, show expectations with pass/fail icons, validator reasoning, expected tool calls, execution failures, and fallback failure summary.
- Render chat transcripts including tool call JSON in the Messages tab.
- Detect global runner errors and expose log toggles and dismissal controls.

## Non-Goals (Current Release)
- Real-time asynchronous execution queue management (future exploration).
- Historical trend reporting or persistent storage of run history.
- Authentication, multi-user collaboration, or RBAC controls.
- Custom theming beyond existing Streamlit capabilities.

## Success Metrics
- Launch command consistently opens the dashboard without manual environment tweaks.
- Test suite re-runs correctly update metrics and cards within a single Streamlit session.
- Users can identify failure reasons (tool mismatch, assertion, expectations) without examining raw stack traces.
- Global errors are surfaced with actionable detail and can be dismissed by the user.

## Risks & Mitigations
- **Streamlit Dependency**: Ensure optional dependency group (`ui`) lists Streamlit and that the CLI warns if it’s missing.
- **Session State Drift**: Reinitialize keys on launch and reset relevant keys after runs to avoid stale selections.
- **Large Suites**: Grid rendering may become slow; mitigate with failing-only filter and future pagination if needed.

## Open Questions
- Should we support multiple project locations or dynamic test discovery paths via UI controls?
- Do we need offline reporting/export (CSV/JSON) from the dashboard?
- What proportion of users rely on the CLI vs. dashboard, informing further investment?
