import { ChangeEvent, useMemo, useRef, useState } from "react";

type UploadPanelProps = {
  onUpload: (files: File[]) => Promise<void> | void;
  isUploading?: boolean;
  error?: string | null;
};

export function UploadPanel({ onUpload, isUploading = false, error }: UploadPanelProps) {
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [localError, setLocalError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const displayError = localError ?? error;

  const selectedSizeLabel = useMemo(
    () =>
      selectedFiles.length
        ? `${selectedFiles.length} file${selectedFiles.length > 1 ? "s" : ""} queued`
        : "Drop one or more PDFs to begin.",
    [selectedFiles],
  );

  const validateFiles = (incomingFiles: File[]) => {
    const invalid = incomingFiles.find(
      (file) => !file.name.toLowerCase().endsWith(".pdf") || file.size > 50 * 1024 * 1024,
    );
    if (invalid) {
      setLocalError("Only PDF files up to 50 MB can be uploaded.");
      return;
    }
    setLocalError(null);
    setSelectedFiles(incomingFiles);
  };

  const handleChange = (event: ChangeEvent<HTMLInputElement>) => {
    validateFiles(Array.from(event.target.files ?? []));
  };

  const handleSubmit = async () => {
    if (!selectedFiles.length) {
      setLocalError("Select at least one PDF before starting the pipeline.");
      return;
    }
    await onUpload(selectedFiles);
    setSelectedFiles([]);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  return (
    <section className="panel upload-panel">
      <div className="panel__heading">
        <div>
          <p className="eyebrow">Ingestion queue</p>
          <h2>Drop source material into the archive</h2>
        </div>
        <span className="pill">{selectedSizeLabel}</span>
      </div>

      <label className="upload-dropzone">
        <input
          ref={fileInputRef}
          type="file"
          accept="application/pdf,.pdf"
          multiple
          onChange={handleChange}
          hidden
        />
        <span>Choose PDFs or drag them in</span>
        <small>Each file is extracted, embedded, and indexed independently.</small>
      </label>

      {selectedFiles.length ? (
        <ul className="upload-list" aria-label="Selected files">
          {selectedFiles.map((file) => (
            <li key={`${file.name}-${file.size}`}>
              <div>
                <strong>{file.name}</strong>
                <small>{Math.ceil(file.size / 1024)} KB</small>
              </div>
              <button
                type="button"
                className="ghost-button"
                onClick={() =>
                  setSelectedFiles((current) => current.filter((item) => item.name !== file.name))
                }
              >
                Remove
              </button>
            </li>
          ))}
        </ul>
      ) : null}

      {displayError ? <p className="form-error">{displayError}</p> : null}

      <div className="upload-actions">
        <button type="button" className="ghost-button" onClick={() => fileInputRef.current?.click()}>
          Browse files
        </button>
        <button type="button" className="primary-button" disabled={isUploading} onClick={handleSubmit}>
          {isUploading ? "Processing…" : "Queue files"}
        </button>
      </div>
    </section>
  );
}

