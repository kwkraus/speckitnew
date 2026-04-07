type StatusBadgeProps = {
  status: "pending" | "processing" | "completed" | "failed" | "deleting";
};

const LABELS: Record<StatusBadgeProps["status"], string> = {
  pending: "Queued",
  processing: "Processing",
  completed: "Indexed",
  failed: "Needs review",
  deleting: "Removing",
};

export function StatusBadge({ status }: StatusBadgeProps) {
  return (
    <span className={`status-badge status-badge--${status}`} role="status">
      {LABELS[status]}
    </span>
  );
}

