import { MessageSchema } from "../services/types";

type MessageBubbleProps = {
  message: MessageSchema;
  onCitationClick: (index: number) => void;
};

export function MessageBubble({ message, onCitationClick }: MessageBubbleProps) {
  return (
    <article className={`message-bubble message-bubble--${message.role}`}>
      <div className="message-bubble__meta">
        <strong>{message.role === "assistant" ? "Archive" : "You"}</strong>
        <span>{new Date(message.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</span>
      </div>

      <p>{message.content}</p>

      {message.citations.length ? (
        <div className="message-bubble__citations">
          {message.citations.map((_, index) => (
            <button key={`${message.id}-${index}`} type="button" onClick={() => onCitationClick(index)}>
              [{index + 1}]
            </button>
          ))}
        </div>
      ) : null}
    </article>
  );
}

