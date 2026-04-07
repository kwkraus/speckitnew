import { DocumentResponse } from "../services/types";
import { EmptyState } from "./EmptyState";
import { StatusBadge } from "./StatusBadge";

type DocumentLibraryProps = {
  documents: DocumentResponse[];
  statusFilter: string;
  onStatusFilterChange: (status: string) => void;
  onDelete: (documentId: string) => Promise<void> | void;
};

export function DocumentLibrary({
  documents,
  statusFilter,
  onStatusFilterChange,
  onDelete,
}: DocumentLibraryProps) {
  if (!documents.length) {
    return (
      <EmptyState
        eyebrow="Library"
        title="No documents in the archive yet"
        copy="Upload a PDF to populate the library and make it available for grounded chat."
      />
    );
  }

  return (
    <section className="panel">
      <div className="panel__heading">
        <div>
          <p className="eyebrow">Library</p>
          <h2>Track every indexed document</h2>
        </div>
        <label className="select-wrap">
          <span>Status</span>
          <select value={statusFilter} onChange={(event) => onStatusFilterChange(event.target.value)}>
            <option value="all">All</option>
            <option value="pending">Queued</option>
            <option value="processing">Processing</option>
            <option value="completed">Indexed</option>
            <option value="failed">Needs review</option>
          </select>
        </label>
      </div>

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Filename</th>
              <th>Status</th>
              <th>Pages</th>
              <th>Uploaded</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {documents.map((document) => (
              <tr key={document.id}>
                <td>
                  <strong>{document.filename}</strong>
                  <p>{document.chunk_count ?? 0} indexed chunks</p>
                </td>
                <td>
                  <StatusBadge status={document.status} />
                </td>
                <td>{document.page_count ?? "—"}</td>
                <td>{new Date(document.created_at).toLocaleDateString()}</td>
                <td>
                  <button
                    type="button"
                    className="ghost-button"
                    onClick={() => {
                      if (window.confirm(`Delete ${document.filename}?`)) {
                        void onDelete(document.id);
                      }
                    }}
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

