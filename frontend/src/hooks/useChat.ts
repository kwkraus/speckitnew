import { useCallback, useEffect, useState } from "react";

import { api } from "../services/api";
import { ConversationResponse, ConversationSummary, MessageSchema } from "../services/types";

export function useChat() {
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<MessageSchema[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSending, setIsSending] = useState(false);

  const loadConversations = useCallback(async () => {
    try {
      setIsLoading(true);
      const response = await api.listConversations();
      setConversations(response.conversations);
      if (!activeConversationId && response.conversations[0]) {
        setActiveConversationId(response.conversations[0].id);
      }
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Unable to load conversations.");
    } finally {
      setIsLoading(false);
    }
  }, [activeConversationId]);

  useEffect(() => {
    void loadConversations();
  }, [loadConversations]);

  useEffect(() => {
    if (!activeConversationId) {
      setMessages([]);
      return;
    }

    void api
      .getConversation(activeConversationId)
      .then((conversation: ConversationResponse) => {
        setMessages(conversation.messages);
        setError(null);
      })
      .catch((loadError) => {
        setError(loadError instanceof Error ? loadError.message : "Unable to load the active conversation.");
      });
  }, [activeConversationId]);

  const createConversation = useCallback(async (): Promise<string> => {
    const conversation = await api.createConversation("New investigation");
    setConversations((current) => [
      {
        id: conversation.id,
        title: conversation.title,
        created_at: conversation.created_at,
        updated_at: conversation.updated_at,
        message_count: 0,
      },
      ...current,
    ]);
    setActiveConversationId(conversation.id);
    setMessages([]);
    return conversation.id;
  }, []);

  const sendMessage = useCallback(async (content: string) => {
    const conversationId = activeConversationId ?? (await createConversation());
    if (!conversationId) {
      return;
    }

    setIsSending(true);
    try {
      const response = await api.sendMessage(conversationId, content);
      setMessages((current) => [...current, response.user_message, response.assistant_message]);
      await loadConversations();
      setError(null);
    } catch (sendError) {
      setError(sendError instanceof Error ? sendError.message : "Unable to send your question.");
      throw sendError;
    } finally {
      setIsSending(false);
    }
  }, [activeConversationId, createConversation, loadConversations]);

  const deleteConversation = useCallback(async (conversationId: string) => {
    await api.deleteConversation(conversationId);
    setConversations((current) => current.filter((conversation) => conversation.id !== conversationId));
    if (activeConversationId === conversationId) {
      setActiveConversationId(null);
      setMessages([]);
    }
  }, [activeConversationId]);

  return {
    conversations,
    activeConversationId,
    setActiveConversationId,
    messages,
    error,
    isLoading,
    isSending,
    createConversation,
    sendMessage,
    deleteConversation,
  };
}

