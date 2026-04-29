"""Threaded mock OIDC Identity Provider for local full E2E load tests."""

# pylint: disable=too-many-instance-attributes,too-many-statements,too-many-return-statements

import base64
import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Lock
from typing import Any
from urllib.parse import parse_qs, urlencode, urlparse
from uuid import uuid4

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa


@dataclass(frozen=True)
class MockIDPSettings:
    """Configuration loaded from environment variables."""

    host: str = os.getenv("OIDC_MOCK_IDP_HOST", "127.0.0.1")
    port: int = int(os.getenv("OIDC_MOCK_IDP_PORT", "9908"))
    issuer: str = os.getenv("OIDC_MOCK_IDP_ISSUER", "http://127.0.0.1:9908")
    client_id: str = os.getenv("OIDC_MOCK_IDP_CLIENT_ID", "accounts-rp")
    client_secret: str = os.getenv(
        "OIDC_MOCK_IDP_CLIENT_SECRET", "accounts-rp-secret"
    )
    sub: str = os.getenv("OIDC_MOCK_IDP_SUB", "loadtest-sub-001")
    email: str = os.getenv("OIDC_MOCK_IDP_EMAIL", "loadtest@example.test")
    first_name: str = os.getenv("OIDC_MOCK_IDP_FIRST_NAME", "Load")
    last_name: str = os.getenv("OIDC_MOCK_IDP_LAST_NAME", "Tester")
    token_ttl_seconds: int = int(os.getenv("OIDC_MOCK_IDP_TOKEN_TTL_SECONDS", "600"))
    kid: str = os.getenv("OIDC_MOCK_IDP_KID", "mock-rs256-key-1")


class MockIDPState:
    """In-memory stores for auth codes and access tokens."""

    def __init__(self):
        self._lock = Lock()
        self.auth_codes: dict[str, dict[str, Any]] = {}
        self.access_tokens: dict[str, dict[str, Any]] = {}

    def put_auth_code(self, code: str, payload: dict[str, Any]) -> None:
        """Store an authorization code payload."""
        with self._lock:
            self.auth_codes[code] = payload

    def pop_auth_code(self, code: str) -> dict[str, Any] | None:
        """Consume an authorization code payload."""
        with self._lock:
            return self.auth_codes.pop(code, None)

    def put_access_token(self, token: str, payload: dict[str, Any]) -> None:
        """Store an access token payload."""
        with self._lock:
            self.access_tokens[token] = payload

    def get_access_token(self, token: str) -> dict[str, Any] | None:
        """Return an access token payload if present."""
        with self._lock:
            return self.access_tokens.get(token)


def _b64url_uint(value: int) -> str:
    raw = value.to_bytes((value.bit_length() + 7) // 8, "big")
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _build_jwks(private_key, kid: str) -> dict[str, Any]:
    public_key = private_key.public_key().public_numbers()
    return {
        "keys": [
            {
                "kty": "RSA",
                "use": "sig",
                "alg": "RS256",
                "kid": kid,
                "n": _b64url_uint(public_key.n),
                "e": _b64url_uint(public_key.e),
            }
        ]
    }


def _json(handler: BaseHTTPRequestHandler, payload: dict[str, Any], status=200) -> None:
    body = json.dumps(payload).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def _redirect(handler: BaseHTTPRequestHandler, location: str) -> None:
    handler.send_response(HTTPStatus.FOUND)
    handler.send_header("Location", location)
    handler.end_headers()


def create_handler(settings: MockIDPSettings, state: MockIDPState, private_key):
    """Return a request handler bound to settings/state/key objects."""

    jwks_payload = _build_jwks(private_key, settings.kid)

    class Handler(BaseHTTPRequestHandler):
        """HTTP handler implementing OIDC endpoints for local tests."""

        def log_message(self, format_, *args):  # noqa: A003
            """Reduce console noise for high-throughput runs."""

        def do_GET(self):  # noqa: N802
            """Handle authorize, jwks, userinfo and health endpoints."""
            parsed = urlparse(self.path)
            query = parse_qs(parsed.query)

            if parsed.path in ("/healthz", "/health"):
                _json(self, {"status": "ok"})
                return

            if parsed.path in ("/.well-known/jwks.json", "/jwks"):
                _json(self, jwks_payload)
                return

            if parsed.path == "/authorize":
                redirect_uri = query.get("redirect_uri", [""])[0]
                state_param = query.get("state", [""])[0]
                nonce = query.get("nonce", [""])[0]
                client_id = query.get("client_id", [""])[0]

                if not redirect_uri or not state_param or not client_id:
                    _json(self, {"error": "invalid_request"}, status=400)
                    return

                if client_id != settings.client_id:
                    _json(self, {"error": "unauthorized_client"}, status=401)
                    return

                code = f"mock-code-{uuid4().hex}"
                state.put_auth_code(
                    code,
                    {
                        "nonce": nonce,
                        "client_id": client_id,
                        "sub": settings.sub,
                        "email": settings.email,
                    },
                )

                separator = "&" if "?" in redirect_uri else "?"
                callback_query = urlencode({"code": code, "state": state_param})
                callback = f"{redirect_uri}{separator}{callback_query}"
                _redirect(self, callback)
                return

            if parsed.path == "/userinfo":
                auth_header = self.headers.get("Authorization", "")
                if not auth_header.startswith("Bearer "):
                    _json(self, {"error": "missing_token"}, status=401)
                    return

                token = auth_header.split(" ", 1)[1]
                payload = state.get_access_token(token)
                if not payload:
                    _json(self, {"error": "invalid_token"}, status=401)
                    return

                _json(
                    self,
                    {
                        "sub": payload["sub"],
                        "email": settings.email,
                        "first_name": settings.first_name,
                        "last_name": settings.last_name,
                    },
                )
                return

            _json(self, {"error": "not_found"}, status=404)

        def do_POST(self):  # noqa: N802
            """Handle token exchange endpoint."""
            parsed = urlparse(self.path)
            if parsed.path != "/token":
                _json(self, {"error": "not_found"}, status=404)
                return

            length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(length).decode("utf-8")
            form = parse_qs(body)

            code = form.get("code", [""])[0]
            client_id = form.get("client_id", [""])[0]
            client_secret = form.get("client_secret", [""])[0]
            grant_type = form.get("grant_type", [""])[0]

            if grant_type != "authorization_code":
                _json(self, {"error": "unsupported_grant_type"}, status=400)
                return
            if client_id != settings.client_id or client_secret != settings.client_secret:
                _json(self, {"error": "invalid_client"}, status=401)
                return

            auth_code_payload = state.pop_auth_code(code)
            if not auth_code_payload:
                _json(self, {"error": "invalid_grant"}, status=400)
                return

            now = datetime.now(tz=UTC)
            id_token_payload = {
                "iss": settings.issuer,
                "sub": auth_code_payload["sub"],
                "aud": client_id,
                "email": settings.email,
                "exp": int((now + timedelta(seconds=settings.token_ttl_seconds)).timestamp()),
                "iat": int(now.timestamp()),
            }
            if auth_code_payload.get("nonce"):
                id_token_payload["nonce"] = auth_code_payload["nonce"]

            id_token = jwt.encode(
                id_token_payload,
                key=private_key,
                algorithm="RS256",
                headers={"kid": settings.kid},
            )

            access_token = f"mock-access-{uuid4().hex}"
            state.put_access_token(access_token, {"sub": auth_code_payload["sub"]})

            _json(
                self,
                {
                    "access_token": access_token,
                    "id_token": id_token,
                    "token_type": "Bearer",
                    "expires_in": settings.token_ttl_seconds,
                },
            )

    return Handler


def create_server(settings: MockIDPSettings | None = None) -> ThreadingHTTPServer:
    """Instantiate a configured HTTP server for the local mock IdP."""
    effective_settings = settings or MockIDPSettings()
    state = MockIDPState()
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    handler = create_handler(effective_settings, state, private_key)
    return ThreadingHTTPServer((effective_settings.host, effective_settings.port), handler)  # type: ignore[arg-type]


def main() -> None:
    """CLI entrypoint to run the mock IdP service."""
    settings = MockIDPSettings()
    server = create_server(settings)
    print(f"Mock OIDC IdP listening on http://{settings.host}:{settings.port}")  # noqa: T201
    server.serve_forever()


if __name__ == "__main__":
    main()


