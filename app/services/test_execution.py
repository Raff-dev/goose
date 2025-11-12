"""Service helpers for executing Goose tests and updating Streamlit state."""

from __future__ import annotations

import traceback
from datetime import datetime

from app import state
from goose.testing import TestDefinition, list_tests, run_single_test, run_tests


def load_tests() -> list[TestDefinition]:
    """Discover available Goose tests."""

    return list_tests()


def execute_run_all_tests() -> None:
    """Run the full Goose test suite and update session state."""

    try:
        results = run_tests()
    except Exception:  # pragma: no cover - unexpected runner errors  # pylint: disable=broad-exception-caught
        state.set_global_error(traceback.format_exc())
    else:
        state.set_global_error(None)
        for result in results:
            state.set_test_result(result.name, result)
            state.clear_test_error(result.name)
    finally:
        state.set_last_run_time(datetime.now())


def execute_single_test(definition: TestDefinition) -> None:
    """Run an individual Goose test and update session state."""

    try:
        result = run_single_test(definition)
    except Exception:  # pragma: no cover - unexpected execution error  # pylint: disable=broad-exception-caught
        state.set_test_error(definition.qualified_name, traceback.format_exc())
    else:
        state.set_test_result(definition.qualified_name, result)
        state.clear_test_error(definition.qualified_name)
        state.set_global_error(None)
    finally:
        state.set_last_run_time(datetime.now())
