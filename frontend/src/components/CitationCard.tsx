import { CitationSchema } from "../services/types";

type CitationCardProps = {
  citation: CitationSchema;
  index: number;
  highlighted?: boolean;
};

export function CitationCard({ citation, index, highlighted = false }: CitationCardProps) {
  return (
    <article className={`citation-card ${highlighted ? "citation-card--active" : ""}`} id={`citation-${index + 1}`}>
      <div className="citation-card__header">
        <span className="pill">[{index + 1}]</span>
        <div>
          <strong>{citation.document_name}</strong>
          <p>
            Page {citation.page_number}
            {citation.section_title ? ` • ${citation.section_title}` : ""}
          </p>
        </div>
      </div>
      <p>{citation.snippet}</p>
      <small>Confidence: {Math.round(citation.relevance * 100)}%</small>
    </article>
  );
}

