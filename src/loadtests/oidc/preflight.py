"""Preflight checks for OIDC load test environment."""

import argparse
from urllib.parse import urlencode, urljoin

import requests


class PreflightError(RuntimeError):
    """Raised when environment is not suitable for OIDC full E2E load tests."""


def _build_authorize_url(host: str, client_id: str, redirect_uri: str, scope: str) -> str:
    query = urlencode(
        {
            "response_type": "code",
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "scope": scope,
        }
    )
    return f"{host}/api/v1.0/o/authorize/?{query}"


def _to_absolute(host: str, location: str) -> str:
    return location if location.startswith("http") else urljoin(f"{host}/", location.lstrip("/"))


def run_preflight(host: str, client_id: str, redirect_uri: str, scope: str, timeout: float) -> None:
    """Validate backend reachability and upstream authorize behavior."""
    session = requests.Session()

    try:
        authorize_response = session.get(
            _build_authorize_url(host, client_id, redirect_uri, scope),
            allow_redirects=False,
            timeout=timeout,
        )
    except requests.RequestException as exc:
        raise PreflightError(
            f"Backend unreachable on {host}: {exc.__class__.__name__}"
        ) from exc

    if authorize_response.status_code not in (301, 302, 303, 307, 308):
        raise PreflightError(
            "Unexpected status on /o/authorize/ "
            f"(expected redirect, got {authorize_response.status_code})"
        )

    location = authorize_response.headers.get("Location", "")
    if not location:
        raise PreflightError("Missing Location header on /o/authorize/ response")

    if "/api/v1.0/login/" in location:
        login_response = session.get(
            _to_absolute(host, location),
            allow_redirects=False,
            timeout=timeout,
        )
        if login_response.status_code not in (301, 302, 303, 307, 308):
            raise PreflightError(
                "Unexpected status on /login/ "
                f"(expected redirect, got {login_response.status_code})"
            )
        location = login_response.headers.get("Location", "")
        if not location:
            raise PreflightError("Missing Location header on /login/ response")

    if "/api/v1.0/oidc/authenticate/" not in location:
        raise PreflightError(
            "Flow did not reach /api/v1.0/oidc/authenticate/ during preflight"
        )

    authenticate_response = session.get(
        _to_absolute(host, location),
        allow_redirects=False,
        timeout=timeout,
    )
    if authenticate_response.status_code not in (301, 302, 303, 307, 308):
        raise PreflightError(
            "Unexpected status on /oidc/authenticate/ "
            f"(expected redirect, got {authenticate_response.status_code})"
        )

    upstream_authorize_url = authenticate_response.headers.get("Location", "")
    if not upstream_authorize_url:
        raise PreflightError("Missing upstream authorize URL in /oidc/authenticate/ response")

    upstream_response = session.get(
        upstream_authorize_url,
        allow_redirects=False,
        timeout=timeout,
    )
    if upstream_response.status_code == 200:
        raise PreflightError(
            "Upstream /authorize returned 200 (interactive login page). "
            "For load tests, configure a non-interactive IdP (mock/Keycloak auto-login) "
            "that redirects back to callback."
        )

    if upstream_response.status_code not in (301, 302, 303, 307, 308):
        raise PreflightError(
            "Unexpected status on upstream /authorize "
            f"(expected redirect, got {upstream_response.status_code})"
        )


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", required=True)
    parser.add_argument("--client-id", default="oidc-test-client")
    parser.add_argument(
        "--redirect-uri", default="https://client.example.test/callback"
    )
    parser.add_argument("--scope", default="openid email")
    parser.add_argument("--timeout", type=float, default=5.0)
    return parser.parse_args()


def main() -> int:
    """Program entrypoint."""
    args = parse_args()
    try:
        run_preflight(
            host=args.host,
            client_id=args.client_id,
            redirect_uri=args.redirect_uri,
            scope=args.scope,
            timeout=args.timeout,
        )
    except PreflightError as exc:
        print(f"OIDC preflight: FAILED - {exc}")  # noqa: T201
        return 1

    print("OIDC preflight: OK")  # noqa: T201
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

