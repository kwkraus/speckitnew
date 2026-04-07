import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { MsalProvider } from "@azure/msal-react";

import App from "./App";
import { authEnabled, msalInstance } from "./services/auth";
import "./styles.css";

const root = ReactDOM.createRoot(document.getElementById("root") as HTMLElement);

const content = (
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>
);

root.render(authEnabled ? <MsalProvider instance={msalInstance}>{content}</MsalProvider> : content);
