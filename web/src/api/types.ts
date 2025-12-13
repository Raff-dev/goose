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

// Chatting types

export interface AgentSummary {
  id: string;
  name: string;
  models: string[];
}

export interface ConversationSummary {
  id: string;
  agent_id: string;
  agent_name: string;
  model: string;
  title: string;
  message_count: number;
  created_at: string;
  updated_at: string;
}

export interface Message {
  type: string;
  content: string;
  tool_calls?: Array<{
    name: string;
    args: Record<string, unknown>;
    id?: string;
  }>;
  tool_name?: string;
  tool_call_id?: string;
  token_usage?: {
    input_tokens: number;
    output_tokens: number;
    total_tokens: number;
  } | null;
}

export interface Conversation {
  id: string;
  agent_id: string;
  agent_name: string;
  model: string;
  title: string;
  messages: Message[];
  created_at: string;
  updated_at: string;
}

export interface CreateConversationRequest {
  agent_id: string;
  model: string;
  title?: string;
}

export interface StreamEvent {
  type: 'message' | 'token' | 'tool_call' | 'tool_output' | 'message_end' | 'error';
  data: Record<string, unknown>;
}
