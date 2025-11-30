---
agent: agent
---

Always reason before writing code and reach conclusions prior to producing the simplified implementation.

## Purpose

-   Reduce complexity without removing features.
-   Delete unused or deprecated code paths; no backward-compat layers.

## Guiding Principles

-   Apply the Zen of Python, especially "Simple is better than complex" and "Flat is better than nested".
-   Keep only comments that explain the current behavior.
-   Ensure main functions have an easy-to-follow flow; refactor when they do not.

## Workflow

1. **Architectural overview**: list the file’s high-level functionalities and define the minimal set of function signatures needed to support them.
2. **Structural cleanup**: inline single-use helpers (especially private ones), remove unnecessary abstractions, and flatten nesting where possible.
3. **Logic polish**: simplify remaining complex branches and, only when it improves readability, extract focused helpers or classes.
4. **Dead-code sweep**: remove unused symbols and code that exists purely for backward compatibility, then update every reference to the simplified implementations.
