import axios, { type AxiosInstance } from "axios";

import type { ToolInvokeResponse, ToolSchema, ToolSummary } from "./types";

export const API_BASE_URL = (import.meta.env.VITE_GOOSE_API_URL as string | undefined)?.replace(/\/+$/, "") || "http://localhost:8730";

const http: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // Longer timeout for tool invocations
});

export const toolingApi = {
  async listTools(): Promise<ToolSummary[]> {
    const response = await http.get<ToolSummary[]>('/tooling/tools');
    return response.data;
  },

  async getToolSchema(name: string): Promise<ToolSchema> {
    const response = await http.get<ToolSchema>(`/tooling/tools/${name}`);
    return response.data;
  },

  async invokeTool(name: string, args: Record<string, unknown>): Promise<ToolInvokeResponse> {
    const response = await http.post<ToolInvokeResponse>(`/tooling/tools/${name}/invoke`, { args });
    return response.data;
  },
};
