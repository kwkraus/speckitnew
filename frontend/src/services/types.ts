export interface DocumentResponse {
  id: string;
  filename: string;
  status: "pending" | "processing" | "completed" | "failed" | "deleting";
  file_size: number;
  page_count?: number | null;
  chunk_count?: number | null;
  error_message?: string | null;
  created_at: string;
  updated_at?: string;
}

export interface StageProgress {
  extraction: string;
  embedding: string;
  indexing: string;
}

export interface DocumentStatusResponse {
  id: string;
  status: DocumentResponse["status"];
  stage: string;
  progress: StageProgress;
  updated_at: string;
  error_message?: string | null;
}

export interface DocumentListResponse {
  documents: DocumentResponse[];
  total: number;
  page: number;
  page_size: number;
}

export interface CitationSchema {
  chunk_id: string;
  document_id: string;
  document_name: string;
  page_number: number;
  section_title?: string | null;
  snippet: string;
  relevance: number;
}

export interface MessageSchema {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations: CitationSchema[];
  created_at: string;
}

export interface ConversationResponse {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  messages: MessageSchema[];
}

export interface ConversationSummary {
  id: string;
  title: string;
  message_count: number;
  created_at: string;
  updated_at: string;
}

export interface ConversationListResponse {
  conversations: ConversationSummary[];
  total: number;
  page: number;
  page_size: number;
}

export interface MessageResponse {
  user_message: MessageSchema;
  assistant_message: MessageSchema;
}

export interface HealthResponse {
  status: "healthy" | "degraded";
  services: Record<string, string>;
}

export interface ErrorResponse {
  error: string;
  message: string;
}

