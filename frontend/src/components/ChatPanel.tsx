import { FormEvent, useMemo, useState } from "react";

import { MessageSchema } from "../services/types";
import { CitationCard } from "./CitationCard";
import { EmptyState } from "./EmptyState";
import { MessageBubble } from "./MessageBubble";

type ChatPanelProps = {
  messages: MessageSchema[];
  onSend: (content: string) => Promise<void> | void;
  isSending?: boolean;
  error?: string | null;
};

export function ChatPanel({ messages, onSend, isSending = false, error }: ChatPanelProps) {
  const [draft, setDraft] = useState("");
  const [activeCitation, setActiveCitation] = useState<number | null>(null);

  const citations = useMemo(
    () => messages.flatMap((message) => message.citations).map((citation, index) => ({ citation, index })),
    [messages],
  );

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (!draft.trim()) {
      return;
    }
    await onSend(draft.trim());
    setDraft("");
  };

  return (
    <section className="panel chat-panel">
      <div className="panel__heading">
        <div>
          <p className="eyebrow">Research console</p>
          <h2>Ask grounded questions</h2>
        </div>
        <span className="pill">{messages.length} messages</span>
      </div>

      {messages.length ? (
        <div className="chat-stream" aria-live="polite">
          {messages.map((message) => (
            <MessageBubble
              key={message.id}
              message={message}
              onCitationClick={(index) => setActiveCitation(index)}
            />
          ))}
          {isSending ? <div className="chat-loading">Generating a cited answer…</div> : null}
        </div>
      ) : (
        <EmptyState
          eyebrow="No thread yet"
          title="Start with a natural-language question"
          copy="The archive responds with evidence-backed answers and page-level citations once your PDFs finish indexing."
        />
      )}

      <form className="chat-composer" onSubmit={handleSubmit}>
        <textarea
          aria-label="Message input"
          placeholder="Ask about trends, contracts, totals, risks, or named entities…"
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          rows={3}
        />
        <button type="submit" className="primary-button" disabled={isSending}>
          Send
        </button>
      </form>

      {error ? <p className="form-error">{error}</p> : null}

      {citations.length ? (
        <div className="citation-grid">
          {citations.map(({ citation, index }) => (
            <CitationCard
              key={`${citation.chunk_id}-${index}`}
              citation={citation}
              index={index}
              highlighted={activeCitation === index}
            />
          ))}
        </div>
      ) : null}
    </section>
  );
}

