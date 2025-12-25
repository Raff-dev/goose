import axios, { type AxiosInstance } from "axios";

import type { JobResource, RunRequestPayload, TestResultModel, TestSummary } from "./types";

export const API_BASE_URL = (import.meta.env.VITE_GOOSE_API_URL as string | undefined)?.replace(/\/+$/, "") || "http://localhost:8730";

const http: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
});

export const apiClient = {
  async listTests(): Promise<TestSummary[]> {
    const response = await http.get<TestSummary[]>('/testing/tests');
    return response.data;
  },

  async listRuns(): Promise<JobResource[]> {
    const response = await http.get<JobResource[]>('/testing/runs');
    return response.data;
  },

  async getRun(id: string): Promise<JobResource> {
    const response = await http.get<JobResource>(`/testing/runs/${id}`);
    return response.data;
  },

  async createRun(payload: RunRequestPayload | undefined = undefined): Promise<JobResource> {
    const body: RunRequestPayload | undefined = payload?.tests?.length ? payload : undefined;
    const response = await http.post<JobResource>('/testing/runs', body);
    return response.data;
  },

  async getHistory(): Promise<Record<string, TestResultModel>> {
    const response = await http.get<Record<string, TestResultModel>>('/testing/history');
    return response.data;
  },

  async getTestHistory(qualifiedName: string): Promise<TestResultModel[]> {
    const response = await http.get<TestResultModel[]>(`/testing/history/${qualifiedName}`);
    return response.data;
  },

  async clearHistory(): Promise<void> {
    await http.delete('/testing/history');
  },

  async clearTestHistory(qualifiedName: string): Promise<void> {
    await http.delete(`/testing/history/${qualifiedName}`);
  },

  async deleteTestRun(qualifiedName: string, index: number): Promise<void> {
    await http.delete(`/testing/history/${qualifiedName}/${index}`);
  },
};
