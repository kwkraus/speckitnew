import { ReactNode } from "react";

type EmptyStateProps = {
  eyebrow: string;
  title: string;
  copy: string;
  action?: ReactNode;
};

export function EmptyState({ eyebrow, title, copy, action }: EmptyStateProps) {
  return (
    <section className="empty-state">
      <p className="eyebrow">{eyebrow}</p>
      <h2>{title}</h2>
      <p>{copy}</p>
      {action ? <div className="empty-state__action">{action}</div> : null}
    </section>
  );
}

