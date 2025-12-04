# Testing Improvements TODOs

| Priority | Size | Task |
|----------|------|------|
| P1 | M | Add abort-execution controls so long-running cases can stop early |
| P1 | M | Stream test results to file for LLM-assisted debugging (live updates as tests run) |
| P1 | S | Add "Copy conversation" button to test detail view |
| P1 | S | Rename "Agent Response" to "Test Output" (or similar) in UI |
| P1 | S | Show live elapsed time for currently running test |
| P2 | L | Run identical cases across a model matrix (mini, standard, etc.) and diff summaries/metrics |
| P2 | M | Run the full suite multiple times to surface flaky behavior |
| P2 | M | Introduce declarative tool-call operators (patterns, `in`, `set`, exact, range, optional) |
| P3 | L | Let testing agents call helper agents/tools for due diligence |
| P3 | M | Evaluate Goose core once per session, not after every test |
| P2 | M | Detect whether failures stem from tool errors or agent reasoning mistakes |
| P1 | L | Async support |

# Bugs

| Priority | Description |
|----------|-------------|
| P1 | Import errors in test code silently fail instead of propagating to user |
| P2 | UnknownTestError not displayed in dashboard UI (e.g., when test file is deleted/renamed) |
