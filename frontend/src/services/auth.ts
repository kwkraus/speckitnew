import { PublicClientApplication } from "@azure/msal-browser";

const clientId = import.meta.env.VITE_AZURE_CLIENT_ID;
const tenantId = import.meta.env.VITE_AZURE_TENANT_ID;
const redirectUri = import.meta.env.VITE_AZURE_REDIRECT_URI ?? "http://localhost:5173/auth/callback";

export const authEnabled = Boolean(clientId && tenantId);

export const msalInstance = new PublicClientApplication({
  auth: {
    clientId: clientId ?? "local-dev-client",
    authority: `https://login.microsoftonline.com/${tenantId ?? "common"}`,
    redirectUri,
  },
});

export async function getAccessToken(): Promise<string> {
  if (!authEnabled) {
    return "local-dev-token";
  }

  const account = msalInstance.getActiveAccount() ?? msalInstance.getAllAccounts()[0];
  if (!account) {
    await msalInstance.loginRedirect({ scopes: ["openid", "profile"] });
    return "";
  }

  const response = await msalInstance.acquireTokenSilent({
    account,
    scopes: ["openid", "profile"],
  });
  return response.accessToken;
}

export function getLocalIdentityHeaders(): Record<string, string> {
  return authEnabled ? {} : { "x-user-id": "local-dev-user", "x-user-name": "Local Analyst" };
}

