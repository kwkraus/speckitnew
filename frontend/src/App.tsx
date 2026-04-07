import { NavLink, Navigate, Route, Routes } from "react-router-dom";

import { ChatPage } from "./pages/ChatPage";
import { DocumentsPage } from "./pages/DocumentsPage";
import { LoginCallback } from "./pages/LoginCallback";

export default function App() {
  return (
    <div className="shell">
      <aside className="shell__sidebar">
        <div>
          <p className="eyebrow">Multi-agent RAG</p>
          <h1>Signal Archive</h1>
          <p className="sidebar-copy">
            Upload PDFs, index evidence, and question your corpus through a grounded research studio.
          </p>
        </div>

        <nav className="shell__nav" aria-label="Primary">
          <NavLink to="/chat">Chat</NavLink>
          <NavLink to="/documents">Documents</NavLink>
        </nav>

        <div className="sidebar-panel">
          <span className="sidebar-panel__label">Mode</span>
          <strong>Grounded Answers</strong>
          <p>Citations, progress tracking, and clean document provenance are built in.</p>
        </div>
      </aside>

      <main className="shell__content">
        <Routes>
          <Route path="/" element={<Navigate to="/chat" replace />} />
          <Route path="/chat" element={<ChatPage />} />
          <Route path="/documents" element={<DocumentsPage />} />
          <Route path="/auth/callback" element={<LoginCallback />} />
        </Routes>
      </main>
    </div>
  );
}

