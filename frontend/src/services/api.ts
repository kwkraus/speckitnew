import {
  ConversationListResponse,
  ConversationResponse,
  DocumentListResponse,
  DocumentStatusResponse,
  ErrorResponse,
  HealthResponse,
  MessageResponse,
} from "./types";
import { authEnabled, getAccessToken, getLocalIdentityHeaders } from "./auth";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1";

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  if (!(init.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }
  Object.entries(getLocalIdentityHeaders()).forEach(([key, value]) => headers.set(key, value));
  if (authEnabled) {
    const token = await getAccessToken();
    if (token) {
      headers.set("Authorization", `Bearer ${token}`);
    }
  }

  const response = await fetch(`${API_BASE_URL}${path}`, { ...init, headers });
  if (!response.ok) {
    const errorBody = (await response.json().catch(() => null)) as ErrorResponse | null;
    throw new Error(errorBody?.message ?? `Request failed with status ${response.status}`);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

export const api = {
  health: () => request<HealthResponse>("/health"),
  listDocuments: (status?: string) =>
    request<DocumentListResponse>(`/documents${status ? `?status=${encodeURIComponent(status)}` : ""}`),
  getDocumentStatus: (documentId: string) => request<DocumentStatusResponse>(`/documents/${documentId}/status`),
  uploadDocuments: async (files: File[]) => {
    const formData = new FormData();
    files.forEach((file) => formData.append("file", file));
    return request<Record<string, unknown> | Array<Record<string, unknown>>>("/documents/upload", {
      method: "POST",
      body: formData,
    });
  },
  deleteDocument: (documentId: string) => request<void>(`/documents/${documentId}`, { method: "DELETE" }),
  replaceDocument: async (documentId: string, file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return request(`/documents/${documentId}/replace`, { method: "POST", body: formData });
  },
  createConversation: (title?: string) =>
    request<ConversationResponse>("/chat/conversations", {
      method: "POST",
      body: JSON.stringify({ title }),
    }),
  listConversations: () => request<ConversationListResponse>("/chat/conversations"),
  getConversation: (conversationId: string) =>
    request<ConversationResponse>(`/chat/conversations/${conversationId}`),
  sendMessage: (conversationId: string, content: string) =>
    request<MessageResponse>(`/chat/conversations/${conversationId}/messages`, {
      method: "POST",
      body: JSON.stringify({ content }),
    }),
  deleteConversation: (conversationId: string) =>
    request<void>(`/chat/conversations/${conversationId}`, { method: "DELETE" }),
};

