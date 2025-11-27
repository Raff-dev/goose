export type JobStatus = "queued" | "running" | "succeeded" | "failed";

export interface TestSummary {
  qualified_name: string;
  module: string;
  name: string;
  docstring?: string | null;
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
  expectations_unmet: string[];
  query?: string | null;
  expectations: string[];
  expected_tool_calls: string[];
  response: Record<string, unknown> | null;
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
