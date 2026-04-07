import { DocumentLibrary } from "../components/DocumentLibrary";
import { UploadPanel } from "../components/UploadPanel";
import { useDocuments } from "../hooks/useDocuments";

export function DocumentsPage() {
  const { documents, error, isLoading, isUploading, statusFilter, setStatusFilter, uploadDocuments, deleteDocument } =
    useDocuments();

  return (
    <div className="documents-layout">
      <UploadPanel onUpload={uploadDocuments} isUploading={isUploading} error={error} />
      {isLoading ? (
        <section className="panel">
          <p>Loading your archive…</p>
        </section>
      ) : (
        <DocumentLibrary
          documents={documents}
          statusFilter={statusFilter}
          onStatusFilterChange={setStatusFilter}
          onDelete={deleteDocument}
        />
      )}
    </div>
  );
}

