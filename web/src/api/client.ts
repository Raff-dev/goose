import axios, { type AxiosInstance } from "axios";

import type { JobResource, RunRequestPayload, TestSummary } from "./types";

export const API_BASE_URL = (import.meta.env.VITE_GOOSE_API_URL as string | undefined)?.replace(/\/+$/, "") || "http://localhost:8000";

const http: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
});

export const apiClient = {
  async listTests(): Promise<TestSummary[]> {
    const response = await http.get<TestSummary[]>('/tests');
    return response.data;
  },

  async listRuns(): Promise<JobResource[]> {
    const response = await http.get<JobResource[]>('/runs');
    return response.data;
  },

  async getRun(id: string): Promise<JobResource> {
    const response = await http.get<JobResource>(`/runs/${id}`);
    return response.data;
  },

  async createRun(payload: RunRequestPayload | undefined = undefined): Promise<JobResource> {
    const body: RunRequestPayload | undefined = payload?.tests?.length ? payload : undefined;
    const response = await http.post<JobResource>('/runs', body);
    return response.data;
  },
};
