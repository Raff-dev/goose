"""Pydantic schemas for Goose FastAPI request and response payloads.

This module exposes lightweight API-facing models used by the FastAPI
endpoints. The models provide deterministic, JSON-serializable views of
internal domain objects such as test definitions, execution records and
background job state. Helper ``from_*`` classmethods convert internal
types (from ``goose.testing.types`` and the job store) into the
corresponding Pydantic models used in API responses.

Keep these models small and stable — they form the contract between the
backend and the frontend UI.
"""

from __future__ import annotations

import inspect
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from goose.api.jobs import Job, JobStatus, TestStatus
from goose.testing.error_type import ErrorType
from goose.testing.types import ExecutionRecord, TestDefinition, TestResult, ValidationResult


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


class ValidationPayload(BaseModel):
    """Serialized representation of a validation outcome.

    This model captures whether a validation succeeded, human-readable
    reasoning text, and any unmet expectations identified by the
    validator. It is primarily used as part of execution record payloads
    returned in test results.
    """

    success: bool
    reasoning: str = ""
    expectations_unmet: list[str] = Field(default_factory=list)
    unmet_expectation_numbers: list[int] = Field(default_factory=list)

    @classmethod
    def from_validation(cls, validation: ValidationResult) -> ValidationPayload:
        """Convert an internal ``ValidationResult`` into the API model.

        The conversion guards against missing optional attributes on the
        validator result so the API receives stable list types.
        """

        return cls(
            success=validation.success,
            reasoning=validation.reasoning,
            expectations_unmet=list(getattr(validation, "expectations_unmet", [])),
            unmet_expectation_numbers=list(getattr(validation, "unmet_expectation_numbers", [])),
        )


class ExecutionRecordModel(BaseModel):
    """Serialized execution history entry for a test run.

    Each execution record represents a single interaction performed as
    part of a test, including the query sent, expectations checked, the
    tool calls that were expected, the raw response payload and any
    validation data.
    """

    query: str
    expectations: list[str]
    expected_tool_calls: list[str]
    response: dict[str, Any] | None = None
    validation: ValidationPayload | None = None
    error: str | None = None
    error_type: ErrorType | None = None

    @classmethod
    def from_execution(cls, execution: ExecutionRecord) -> ExecutionRecordModel:
        """Build an ``ExecutionRecordModel`` from an internal record.

        Converts nested response and validation objects into plain
        serializable structures suitable for JSON responses.
        """

        response_payload = execution.response.model_dump() if execution.response is not None else None
        validation_payload = (
            ValidationPayload.from_validation(execution.validation) if execution.validation is not None else None
        )
        return cls(
            query=execution.query,
            expectations=list(execution.expectations),
            expected_tool_calls=list(execution.expected_tool_calls),
            response=response_payload,
            validation=validation_payload,
            error=execution.error,
            error_type=execution.error_type,
        )


class TestResultModel(BaseModel):
    """Serialized result for a Goose test execution.

    Contains a summary of whether the test passed, the execution
    duration, an optional error message and the sequence of
    ``ExecutionRecordModel`` entries that were produced while running
    the test.
    """

    qualified_name: str
    module: str
    name: str
    passed: bool
    duration: float
    error: str | None = None
    error_type: ErrorType | None = None
    executions: list[ExecutionRecordModel] = Field(default_factory=list)

    @classmethod
    def from_result(cls, result: TestResult) -> TestResultModel:
        """Convert an internal ``TestResult`` into the API model.

        This method maps nested execution records and pulls identifying
        information from the associated test definition so the API can
        present a self-contained result object.
        """

        executions = [ExecutionRecordModel.from_execution(result.execution)]
        definition = result.definition
        return cls(
            qualified_name=definition.qualified_name,
            module=definition.module,
            name=definition.name,
            passed=result.passed,
            duration=result.duration,
            error=result.error,
            error_type=result.error_type,
            executions=executions,
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
    "ExecutionRecordModel",
    "JobResource",
    "RunRequest",
    "TestResultModel",
    "TestSummary",
    "ValidationPayload",
]
