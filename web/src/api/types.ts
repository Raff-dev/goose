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
  total_tokens: number;
  error: string | null;
  error_type?: ErrorType | null;
  expectations_unmet: string[];
  failure_reasons: Record<string, string>;
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

// Tooling types

export interface ToolParameter {
  name: string;
  type: string;
  description: string;
  required: boolean;
  default?: unknown;
}

export interface ToolSchema {
  name: string;
  description: string;
  parameters: ToolParameter[];
}

export interface ToolSummary {
  name: string;
  description: string;
  parameter_count: number;
}

export interface ToolInvokeResponse {
  success: boolean;
  result?: unknown;
  error?: string;
}
