import { useEffect } from "react";
import { useNavigate } from "react-router-dom";

import { authEnabled, msalInstance } from "../services/auth";

export function LoginCallback() {
  const navigate = useNavigate();

  useEffect(() => {
    if (!authEnabled) {
      navigate("/chat", { replace: true });
      return;
    }

    void msalInstance.handleRedirectPromise().finally(() => {
      navigate("/chat", { replace: true });
    });
  }, [navigate]);

  return (
    <div className="auth-card">
      <p className="eyebrow">Signal Archive</p>
      <h1>Finishing secure sign-in…</h1>
      <p>We are restoring your workspace and routing you back to the archive.</p>
    </div>
  );
}

