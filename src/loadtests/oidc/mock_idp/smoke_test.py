"""Quick smoke test for the local OIDC mock IdP."""

import json
import threading
from urllib.parse import parse_qs, urlparse
from urllib.request import HTTPErrorProcessor, Request, build_opener, urlopen

try:
    from .server import MockIDPSettings, create_server
except ImportError:  # pragma: no cover
    from server import MockIDPSettings, create_server


class _NoRedirect(HTTPErrorProcessor):
    """Return redirect responses as-is instead of following them."""

    def http_response(self, request, response):
        return response

    https_response = http_response


def _get_json(url: str):
    with urlopen(url) as response:  # noqa: S310
        return json.loads(response.read().decode("utf-8"))


def main() -> None:  # pylint: disable=too-many-locals
    """Run an in-process smoke test against all mock IdP endpoints."""
    settings = MockIDPSettings(port=9910, issuer="http://127.0.0.1:9910")
    server = create_server(settings)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        assert _get_json("http://127.0.0.1:9910/healthz")["status"] == "ok"
        jwks = _get_json("http://127.0.0.1:9910/jwks")
        assert jwks["keys"], "JWKS must return at least one key"

        authorize_url = (
            "http://127.0.0.1:9910/authorize"
            "?response_type=code"
            "&client_id=accounts-rp"
            "&redirect_uri=http://127.0.0.1:9901/api/v1.0/oidc/callback/"
            "&scope=openid+email"
            "&state=smoke-state"
        )
        request = Request(authorize_url, method="GET")
        opener = build_opener(_NoRedirect)
        with opener.open(request) as response:  # noqa: S310
            callback_location = response.headers.get("Location", "")
        callback_query = parse_qs(urlparse(callback_location).query)
        code = callback_query.get("code", [""])[0]
        assert code, "Authorize endpoint must return an auth code"

        token_body = (
            "grant_type=authorization_code"
            f"&code={code}"
            "&client_id=accounts-rp"
            "&client_secret=accounts-rp-secret"
            "&redirect_uri=http://127.0.0.1:9901/api/v1.0/oidc/callback/"
        ).encode("utf-8")
        token_request = Request(
            "http://127.0.0.1:9910/token",
            data=token_body,
            method="POST",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        with urlopen(token_request) as response:  # noqa: S310
            token_payload = json.loads(response.read().decode("utf-8"))
        assert "access_token" in token_payload and "id_token" in token_payload

        userinfo_request = Request(
            "http://127.0.0.1:9910/userinfo",
            method="GET",
            headers={"Authorization": f"Bearer {token_payload['access_token']}"},
        )
        with urlopen(userinfo_request) as response:  # noqa: S310
            userinfo_payload = json.loads(response.read().decode("utf-8"))
        assert userinfo_payload["sub"] == settings.sub

    finally:
        server.shutdown()
        server.server_close()

    print("mock-idp smoke test: OK")  # noqa: T201


if __name__ == "__main__":
    main()
