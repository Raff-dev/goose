export type JobStatus = "queued" | "running" | "succeeded" | "failed";

export interface TestSummary {
  qualified_name: string;
  module: string;
  name: string;
  docstring?: string | null;
}

export interface ValidationPayload {
  success: boolean;
  reasoning: string;
  expectations_unmet: string[];
  unmet_expectation_numbers: number[];
}

export interface ExecutionRecordModel {
  query: string;
  expectations: string[];
  expected_tool_calls: string[];
  response: Record<string, unknown> | null;
  validation: ValidationPayload | null;
  error: string | null;
  /** Optional explicit failure classification supplied by the API. */
  error_type?: ErrorType | null;
}

export enum ErrorType {
  Expectation = 'expectation',
  Validation = 'validation',
  ToolCall = 'tool_call',
  Unexpected = 'unexpected',
}

export interface TestResultModel {
  qualified_name: string;
  module: string;
  name: string;
  passed: boolean;
  duration: number;
  error: string | null;
  error_type?: ErrorType | null;
  executions: ExecutionRecordModel[];
}

export type TestStatus = "queued" | "running" | "passed" | "failed";

export interface JobResource {
  id: string;
  status: JobStatus;
  tests: string[];
  created_at: string;
  updated_at: string;
  error: string | null;
  results: TestResultModel[];
  test_statuses: Record<string, TestStatus>;
}

export interface RunRequestPayload {
  tests?: string[] | null;
}
