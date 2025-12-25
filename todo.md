# Testing Improvements TODOs

## � Urgent + Important (Do First)
| Size | Task |
|------|------|
| S | Fix Tooling page showing "network error" instead of actual error details |
| S | Persist Tooling inputs/outputs when switching tabs (avoid reload on tab change) |
| M | Add abort-execution controls so long-running cases can stop early |
| M | Add streaming to the testing module (live updates as agent responds) |
| L | Async support |

## �📋 Important + Not Urgent (Schedule)
| Size | Task |
|------|------|
| M | Stream test results to file for LLM-assisted debugging (live updates as tests run) |
| M | Chatting module - interactive CLI/UI to interact with the agents directly |
| S | Store config in pyproject.toml [tool.goose] (tests_root, reload_targets) |
| M | Detect whether failures stem from tool errors or agent reasoning mistakes |
| M | Anomaly detection - surface unexpected deviations that derailed the intended flow |
| M | Hallucination detection - flag when agent uses information not present in tool outputs or context |

## ⚡ Urgent + Less Important (Quick Wins)
| Size | Task |
|------|------|
| S | Add "Copy conversation" button to Thread section |
| S | Show live elapsed time for currently running test |
| S | Support markdown rendering in error details |
| S | Support markdown rendering in tool invocation results |

## 📦 Not Urgent + Less Important (Backlog)
| Size | Task |
|------|------|
| L | Run identical cases across a model matrix (mini, standard, etc.) and diff summaries/metrics |
| M | Run the full suite multiple times to surface flaky behavior |
| M | Introduce declarative tool-call operators (patterns, `in`, `set`, exact, range, optional) |
| L | Let testing agents call helper agents/tools for due diligence |
| M | Evaluate Goose core once per session, not after every test |
| L | Overview module - save test execution data to files, analytical dashboards with tables and graphs |


# Goose Home Page!
