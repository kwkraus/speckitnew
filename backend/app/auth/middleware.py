import base64
import json
import time
from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.config import Settings


class AuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, settings: Settings) -> None:
        super().__init__(app)
        self.settings = settings

    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        if request.url.path in {"/docs", "/openapi.json", "/api/v1/health"}:
            return await call_next(request)

        if not self.settings.enable_auth:
            request.state.user = {
                "user_id": request.headers.get("x-user-id", "local-dev-user"),
                "display_name": request.headers.get("x-user-name", "Local User"),
            }
            return await call_next(request)

        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={
                    "error": "unauthorized",
                    "message": "Valid authentication token required.",
                },
            )

        token = auth_header.removeprefix("Bearer ").strip()
        claims = self._decode_unverified_claims(token)
        if claims is None:
            return JSONResponse(
                status_code=401,
                content={"error": "unauthorized", "message": "Valid authentication token required."},
            )

        if "exp" in claims and int(claims["exp"]) < int(time.time()):
            return JSONResponse(
                status_code=401,
                content={"error": "unauthorized", "message": "Authentication token has expired."},
            )

        expected_tenant = self.settings.azure_tenant_id
        expected_audience = self.settings.azure_client_id
        if expected_tenant and claims.get("tid") not in {"", expected_tenant}:
            return JSONResponse(
                status_code=401,
                content={"error": "unauthorized", "message": "Token tenant is not allowed."},
            )
        if expected_audience and claims.get("aud") not in {"", expected_audience}:
            return JSONResponse(
                status_code=401,
                content={"error": "unauthorized", "message": "Token audience is not allowed."},
            )

        request.state.user = {
            "user_id": claims.get("oid") or claims.get("sub") or "unknown-user",
            "display_name": claims.get("name") or claims.get("preferred_username") or "Authenticated User",
        }
        return await call_next(request)

    @staticmethod
    def _decode_unverified_claims(token: str) -> dict[str, Any] | None:
        parts = token.split(".")
        if len(parts) != 3:
            return None

        payload = parts[1]
        padding = "=" * (-len(payload) % 4)
        try:
            decoded = base64.urlsafe_b64decode(payload + padding).decode("utf-8")
            return json.loads(decoded)
        except (ValueError, json.JSONDecodeError):
            return None

