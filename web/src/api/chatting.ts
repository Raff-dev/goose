import axios, { type AxiosInstance } from "axios";

import type {
    AgentSummary,
    Conversation,
    ConversationSummary,
    CreateConversationRequest,
} from "./types";

export const API_BASE_URL =
  (import.meta.env.VITE_GOOSE_API_URL as string | undefined)?.replace(/\/+$/, "") ||
  "http://localhost:8730";

const http: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
});

export const chattingApi = {
  async listAgents(): Promise<AgentSummary[]> {
    const response = await http.get<AgentSummary[]>("/chatting/agents");
    return response.data;
  },

  async getAgent(agentId: string): Promise<AgentSummary> {
    const response = await http.get<AgentSummary>(`/chatting/agents/${agentId}`);
    return response.data;
  },

  async listConversations(): Promise<ConversationSummary[]> {
    const response = await http.get<ConversationSummary[]>("/chatting/conversations");
    return response.data;
  },

  async createConversation(request: CreateConversationRequest): Promise<Conversation> {
    const response = await http.post<Conversation>("/chatting/conversations", request);
    return response.data;
  },

  async getConversation(id: string): Promise<Conversation> {
    const response = await http.get<Conversation>(`/chatting/conversations/${id}`);
    return response.data;
  },

  async deleteConversation(id: string): Promise<void> {
    await http.delete(`/chatting/conversations/${id}`);
  },

  getWebSocketUrl(conversationId: string): string {
    const wsBase = API_BASE_URL.replace(/^http/, "ws");
    return `${wsBase}/chatting/ws/conversations/${conversationId}`;
  },
};
