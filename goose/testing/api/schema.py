"""Pydantic schemas for Goose FastAPI request and response payloads.

This module exposes lightweight API-facing models used by the FastAPI
endpoints. The models provide deterministic, JSON-serializable views of
internal domain objects such as test definitions, execution records and
background job state. Helper ``from_*`` classmethods convert internal
types (from ``goose.testing.models.tests`` and the job store) into the
corresponding Pydantic models used in API responses.

Keep these models small and stable — they form the contract between the
backend and the frontend UI.
"""

from __future__ import annotations

import inspect
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from goose.testing.api.jobs import Job, JobStatus, TestStatus
from goose.testing.errors import ErrorType
from goose.testing.models.tests import TestDefinition, TestResult


def _first_line(text: str | None) -> str | None:
    """Return the first non-empty line from *text* or ``None``.

    This helper is used to extract a concise one-line summary from
    potentially multi-line docstrings for inclusion in API responses.
    """

    if not text:
        return None
    return text.strip().splitlines()[0]


class TestSummary(BaseModel):
    """Summarized metadata about a discovered Goose test.

    Fields describe the test's identity and an optional one-line
    docstring. Use ``TestSummary.from_definition`` to build an instance
    from a discovered ``TestDefinition``.
    """

    __test__ = False

    qualified_name: str
    module: str
    name: str
    docstring: str | None = Field(default=None, description="First line of the test docstring, if present")

    model_config = ConfigDict(populate_by_name=True)

    @classmethod
    def from_definition(cls, definition: TestDefinition) -> TestSummary:
        """Create a ``TestSummary`` from a ``TestDefinition``.

        Args:
            definition: The discovered test definition object.

        Returns:
            A populated ``TestSummary`` with the first line of the
            test function's docstring (if present).
        """

        docstring = inspect.getdoc(definition.func)
        return cls(
            qualified_name=definition.qualified_name,
            module=definition.module,
            name=definition.name,
            docstring=_first_line(docstring),
        )


class TestResultModel(BaseModel):
    """Serialized result for a Goose test execution.

    Contains a summary of whether the test passed, the execution
    duration, any captured error metadata, and the recorded test case
    context (query, expectations, expected tool calls, response).
    """

    __test__ = False

    qualified_name: str
    module: str
    name: str
    passed: bool
    duration: float
    total_tokens: int = 0
    error: str | None = None
    error_type: ErrorType | None = None
    expectations_unmet: list[str] = Field(default_factory=list)
    failure_reasons: dict[str, str] = Field(default_factory=dict)
    query: str | None = None
    expectations: list[str] = Field(default_factory=list)
    expected_tool_calls: list[str] = Field(default_factory=list)
    response: dict[str, Any] | None = None

    @classmethod
    def from_result(cls, result: TestResult) -> TestResultModel:
        """Convert an internal ``TestResult`` into the API model.

        This method maps nested execution records and pulls identifying
        information from the associated test definition so the API can
        present a self-contained result object.
        """

        definition = result.definition
        test_case = result.test_case
        query: str | None = None
        expectations: list[str] = []
        expected_tool_calls: list[str] = []
        response_payload: dict[str, Any] | None = None

        if test_case is not None:
            query = test_case.query_message
            expectations = list(test_case.expectations)
            expected_tool_calls = test_case.expected_tool_call_names
            if test_case.last_response is not None:
                response_payload = test_case.last_response.model_dump(mode="json")

        return cls(
            qualified_name=definition.qualified_name,
            module=definition.module,
            name=definition.name,
            passed=result.passed,
            duration=result.duration,
            total_tokens=result.total_tokens,
            error=result.error_message,
            error_type=result.error_type,
            expectations_unmet=list(result.expectations_unmet),
            failure_reasons=dict(result.failure_reasons),
            query=query,
            expectations=expectations,
            expected_tool_calls=expected_tool_calls,
            response=response_payload,
        )


class JobResource(BaseModel):
    """API representation of a background execution job.

    The model exposes both job-level metadata and per-test statuses so
    the frontend can display progress for long-running executions.
    Use ``JobResource.from_job`` to create an instance from the in-memory
    ``Job`` object.
    """

    id: str
    status: JobStatus
    tests: list[str]
    created_at: datetime
    updated_at: datetime
    error: str | None = None
    results: list[TestResultModel] = Field(default_factory=list)
    test_statuses: dict[str, TestStatus] = Field(default_factory=dict)

    model_config = ConfigDict(use_enum_values=True)

    @classmethod
    def from_job(cls, job: Job) -> JobResource:
        """Create a ``JobResource`` from an internal ``Job`` snapshot.

        Converts job targets and results into serializable forms and
        forwards the per-test status mapping for client-side progress
        updates.
        """

        return cls(
            id=job.id,
            status=job.status,
            tests=[target.qualified_name for target in job.targets],
            created_at=job.created_at,
            updated_at=job.updated_at,
            error=job.error,
            results=[TestResultModel.from_result(result) for result in job.results],
            test_statuses=job.test_statuses,
        )


class RunRequest(BaseModel):
    """Request payload for scheduling a new execution job."""

    tests: list[str] | None = Field(
        default=None,
        description="Qualified test names to execute. When omitted, all tests are run.",
    )

    model_config = ConfigDict(extra="forbid")

    # The RunRequest model intentionally forbids extra fields to keep the
    # API surface minimal and explicit. When `tests` is omitted the API
    # interprets that as a request to run the entire discovered test set.


__all__ = [
    "JobResource",
    "RunRequest",
    "TestResultModel",
    "TestSummary",
]
