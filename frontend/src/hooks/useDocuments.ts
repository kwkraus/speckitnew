import { useCallback, useEffect, useMemo, useState } from "react";

import { api } from "../services/api";
import { DocumentResponse } from "../services/types";

export function useDocuments() {
  const [documents, setDocuments] = useState<DocumentResponse[]>([]);
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isUploading, setIsUploading] = useState(false);

  const loadDocuments = useCallback(async () => {
    try {
      setIsLoading(true);
      const response = await api.listDocuments(statusFilter === "all" ? undefined : statusFilter);
      setDocuments(response.documents);
      setError(null);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Unable to load documents.");
    } finally {
      setIsLoading(false);
    }
  }, [statusFilter]);

  useEffect(() => {
    void loadDocuments();
  }, [loadDocuments]);

  useEffect(() => {
    const interval = window.setInterval(() => {
      if (documents.some((document) => document.status === "pending" || document.status === "processing")) {
        void loadDocuments();
      }
    }, 5000);

    return () => window.clearInterval(interval);
  }, [documents, loadDocuments]);

  const uploadDocuments = useCallback(async (files: File[]) => {
    if (!files.length) {
      return;
    }
    setIsUploading(true);
    try {
      await api.uploadDocuments(files);
      await loadDocuments();
      setError(null);
    } catch (uploadError) {
      setError(uploadError instanceof Error ? uploadError.message : "Unable to upload documents.");
      throw uploadError;
    } finally {
      setIsUploading(false);
    }
  }, [loadDocuments]);

  const deleteDocument = useCallback(async (documentId: string) => {
    await api.deleteDocument(documentId);
    await loadDocuments();
  }, [loadDocuments]);

  return {
    documents,
    error,
    isLoading,
    isUploading,
    statusFilter,
    setStatusFilter,
    uploadDocuments,
    deleteDocument,
    refreshDocuments: loadDocuments,
    completedCount: useMemo(
      () => documents.filter((document) => document.status === "completed").length,
      [documents],
    ),
  };
}

