from __future__ import annotations

from goose.testing.errors import ExpectationValidationError, ToolCallValidationError
from goose.testing.test_case import TestCase


def make_case() -> TestCase:
    return TestCase(query_message="hello", expectations=["say hi"], expected_tool_calls=None)


def test_validate_tool_calls_detects_missing():
    case = make_case()
    case.expected_tool_calls = [type("Tool", (), {"name": "search"})()]

    case.validate_tool_calls(actual_tool_call_names=["search"])


def test_validate_tool_calls_allows_extra_tools():
    """Extra tool calls beyond expected should not raise an error."""
    case = make_case()
    case.expected_tool_calls = [type("Tool", (), {"name": "search"})()]

    # Agent called search (expected) plus lookup (extra) - should pass
    case.validate_tool_calls(actual_tool_call_names=["search", "lookup"])


def test_validate_tool_calls_raises_when_mismatch():
    case = make_case()
    case.expected_tool_calls = [type("Tool", (), {"name": "search"})()]

    try:
        case.validate_tool_calls(actual_tool_call_names=[])
    except ToolCallValidationError as error:
        assert "search" in str(error)
    else:  # pragma: no cover - ensures exception is raised
        raise AssertionError("Expected ToolCallValidationError")


def test_validate_expectations_records_unmet():
    case = make_case()
    evaluation = type(
        "Evaluation",
        (),
        {
            "success": False,
            "reasoning": "Missing greeting",
            "expectations_unmet": ["say hi"],
            "unmet_expectation_numbers": [1],
            "failure_reasons": {1: "Agent did not say hi"},
        },
    )

    try:
        case.validate_expectations(evaluation=evaluation())
    except ExpectationValidationError as error:
        assert "Missing greeting" in error.reasoning
        assert error.expectations_unmet == ["say hi"]
        assert error.failure_reasons == {"say hi": "Agent did not say hi"}
    else:  # pragma: no cover
        raise AssertionError("Expected ExpectationValidationError")


def test_expected_tool_calls_rejects_non_tools():
    """Passing non-BaseTool items to expected_tool_calls should raise TypeError."""
    import types

    fake_module = types.ModuleType("fake_tools")

    try:
        TestCase(
            query_message="test",
            expectations=["test"],
            expected_tool_calls=[fake_module],  # type: ignore[list-item]
        )
    except TypeError as error:
        assert "expected_tool_calls must contain BaseTool instances" in str(error)
        assert "module" in str(error)
    else:  # pragma: no cover
        raise AssertionError("Expected TypeError for non-tool item")


def test_expected_tool_calls_rejects_plain_functions():
    """Passing plain functions (not decorated with @tool) should raise TypeError."""

    def my_function():
        pass

    try:
        TestCase(
            query_message="test",
            expectations=["test"],
            expected_tool_calls=[my_function],  # type: ignore[list-item]
        )
    except TypeError as error:
        assert "expected_tool_calls must contain BaseTool instances" in str(error)
        assert "function" in str(error)
    else:  # pragma: no cover
        raise AssertionError("Expected TypeError for plain function")
