import { ChatPanel } from "../components/ChatPanel";
import { EmptyState } from "../components/EmptyState";
import { useChat } from "../hooks/useChat";
import { useDocuments } from "../hooks/useDocuments";

export function ChatPage() {
  const { messages, error, isSending, conversations, activeConversationId, setActiveConversationId, createConversation, sendMessage, deleteConversation } =
    useChat();
  const { completedCount } = useDocuments();

  return (
    <div className="page-grid">
      <section className="panel conversation-panel">
        <div className="panel__heading">
          <div>
            <p className="eyebrow">Threads</p>
            <h2>Investigation lanes</h2>
          </div>
          <button type="button" className="ghost-button" onClick={() => void createConversation()}>
            New
          </button>
        </div>

        <div className="metric-card">
          <span>Indexed documents</span>
          <strong>{completedCount}</strong>
        </div>

        {conversations.length ? (
          <ul className="conversation-list">
            {conversations.map((conversation) => (
              <li key={conversation.id} className={conversation.id === activeConversationId ? "is-active" : ""}>
                <button type="button" onClick={() => setActiveConversationId(conversation.id)}>
                  <strong>{conversation.title}</strong>
                  <small>{conversation.message_count} messages</small>
                </button>
                <button
                  type="button"
                  className="ghost-button"
                  onClick={() => void deleteConversation(conversation.id)}
                >
                  ×
                </button>
              </li>
            ))}
          </ul>
        ) : (
          <EmptyState
            eyebrow="No threads"
            title="Create your first research lane"
            copy="Each thread keeps its own context so you can compare documents, ask follow-ups, and manage separate investigations."
            action={
              <button type="button" className="primary-button" onClick={() => void createConversation()}>
                Start a conversation
              </button>
            }
          />
        )}
      </section>

      <ChatPanel messages={messages} onSend={sendMessage} isSending={isSending} error={error} />
    </div>
  );
}

