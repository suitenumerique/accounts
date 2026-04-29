"""Reusable scenario logic for OIDC load tests."""

from time import perf_counter
from urllib.parse import parse_qs, urlencode, urlparse

from locust import events

try:
    from .config import OIDCLoadTestConfig
except ImportError:  # pragma: no cover
    from config import OIDCLoadTestConfig


class OIDCFlowError(RuntimeError):
    """Raised when a load-test step does not match the expected OIDC flow."""


def build_authorize_url(config: OIDCLoadTestConfig) -> str:
    """Build the OAuth2 authorize URL used by product applications."""
    query = urlencode(
        {
            "response_type": "code",
            "client_id": config.client_id,
            "redirect_uri": config.redirect_uri,
            "scope": config.scope,
        }
    )
    return f"{config.authorize_path}?{query}"


def to_local_path(url_or_path: str) -> str:
    """Convert absolute URL to path+query for local backend requests."""
    parsed = urlparse(url_or_path)
    if not parsed.scheme:
        return url_or_path
    path = parsed.path or "/"
    return f"{path}?{parsed.query}" if parsed.query else path


def _extract_authorization_code(redirect_url: str, expected_redirect_uri: str) -> str:
    if not redirect_url.startswith(expected_redirect_uri):
        raise OIDCFlowError(
            f"final redirect should start with {expected_redirect_uri}, got {redirect_url}"
        )
    params = parse_qs(urlparse(redirect_url).query)
    code = params.get("code", [""])[0]
    if not code:
        raise OIDCFlowError("authorization code missing in final redirect")
    return code


def _follow_redirect_chain_to_product(user, start_location: str, config: OIDCLoadTestConfig) -> str:
    location = start_location
    for _ in range(config.max_redirect_hops):
        if location.startswith(config.redirect_uri):
            return location

        response = user.client.get(
            to_local_path(location),
            allow_redirects=False,
            name="GET post-login redirect",
        )
        if response.status_code not in (301, 302, 303, 307, 308):
            break

        location = response.headers.get("Location", "")
        if not location:
            raise OIDCFlowError("redirect response missing Location header")

    # Fallback: now that the user should be logged in, request authorize again.
    response = user.client.get(
        build_authorize_url(config),
        allow_redirects=False,
        name="GET /api/v1.0/o/authorize/ (post-login)",
    )
    if response.status_code != 302:
        raise OIDCFlowError(
            "post-login authorize should return 302, "
            f"got {response.status_code}"
        )

    final_location = response.headers.get("Location", "")
    if not final_location:
        raise OIDCFlowError("post-login authorize redirect missing Location")
    return final_location


def _exchange_code_for_tokens(user, config: OIDCLoadTestConfig, authorization_code: str) -> None:
    response = user.client.post(
        config.token_path,
        data={
            "grant_type": "authorization_code",
            "code": authorization_code,
            "redirect_uri": config.redirect_uri,
            "client_id": config.client_id,
            "client_secret": config.client_secret,
        },
        name="POST /api/v1.0/o/token/",
    )
    if response.status_code != 200:
        raise OIDCFlowError(f"token exchange should return 200, got {response.status_code}")

    payload = response.json()
    if "access_token" not in payload or "id_token" not in payload:
        raise OIDCFlowError("token payload must contain access_token and id_token")


def run_full_e2e_new_session_flow(user, config: OIDCLoadTestConfig) -> None:  # pylint: disable=too-many-branches,too-many-locals,too-many-statements
    """Run full E2E flow for a user without active session."""
    start = perf_counter()
    name = "full-e2e:new-session"

    try:
        user.client.cookies.clear()

        authorize_response = user.client.get(
            build_authorize_url(config),
            allow_redirects=False,
            name="GET /api/v1.0/o/authorize/",
        )
        if authorize_response.status_code != 302:
            raise OIDCFlowError(
                f"authorize should return 302, got {authorize_response.status_code}"
            )

        location = authorize_response.headers.get("Location", "")
        if not location:
            raise OIDCFlowError("authorize redirect is missing Location header")

        if config.login_path in location:
            login_response = user.client.get(
                to_local_path(location),
                allow_redirects=False,
                name="GET /api/v1.0/login/",
            )
            if login_response.status_code != 302:
                raise OIDCFlowError(
                    f"login should return 302, got {login_response.status_code}"
                )
            location = login_response.headers.get("Location", "")
            if not location:
                raise OIDCFlowError("login redirect is missing Location header")

        if config.authenticate_path not in location:
            raise OIDCFlowError(
                "redirect chain did not reach /api/v1.0/oidc/authenticate/"
            )

        authenticate_response = user.client.get(
            to_local_path(location),
            allow_redirects=False,
            name="GET /api/v1.0/oidc/authenticate/",
        )
        if authenticate_response.status_code != 302:
            raise OIDCFlowError(
                "oidc/authenticate should return 302 to upstream IdP, "
                f"got {authenticate_response.status_code}"
            )

        upstream_location = authenticate_response.headers.get("Location", "")
        if not upstream_location:
            raise OIDCFlowError("oidc/authenticate redirect is missing Location header")

        if config.expected_upstream_issuer and not upstream_location.startswith(
            config.expected_upstream_issuer
        ):
            raise OIDCFlowError(
                "upstream redirect does not match expected issuer: "
                f"{upstream_location}"
            )

        state = parse_qs(urlparse(upstream_location).query).get("state", [""])[0]
        if not state:
            raise OIDCFlowError("upstream authorize redirect should include a state")

        upstream_authorize_response = user.client.get(
            upstream_location,
            allow_redirects=False,
            name="GET upstream /authorize",
        )
        if upstream_authorize_response.status_code != 302:
            raise OIDCFlowError(
                "upstream authorize should redirect to callback, "
                f"got {upstream_authorize_response.status_code}"
            )

        callback_location = upstream_authorize_response.headers.get("Location", "")
        if not callback_location:
            raise OIDCFlowError("upstream authorize redirect missing callback Location")

        callback_response = user.client.get(
            to_local_path(callback_location),
            allow_redirects=False,
            name="GET /api/v1.0/oidc/callback/",
        )
        if callback_response.status_code not in (200, 302):
            raise OIDCFlowError(
                "callback should return 200 or 302, "
                f"got {callback_response.status_code}"
            )

        if callback_response.status_code == 302:
            next_location = callback_response.headers.get("Location", "")
            if not next_location:
                raise OIDCFlowError("callback redirect missing Location header")
            final_redirect = _follow_redirect_chain_to_product(user, next_location, config)
        else:
            final_redirect = _follow_redirect_chain_to_product(
                user, build_authorize_url(config), config
            )

        code = _extract_authorization_code(final_redirect, config.redirect_uri)
        _exchange_code_for_tokens(user, config, code)

    except Exception as exc:  # noqa: BLE001
        events.request.fire(
            request_type="FLOW",
            name=name,
            response_time=(perf_counter() - start) * 1000,
            response_length=0,
            exception=exc,
        )
        raise

    events.request.fire(
        request_type="FLOW",
        name=name,
        response_time=(perf_counter() - start) * 1000,
        response_length=0,
        exception=None,
    )

def run_existing_session_flow(user, config: OIDCLoadTestConfig) -> None:
    """Run full E2E flow for a user expected to already have an active session."""
    start = perf_counter()
    name = "full-e2e:existing-session"

    try:
        authorize_response = user.client.get(
            build_authorize_url(config),
            allow_redirects=False,
            name="GET /api/v1.0/o/authorize/",
        )
        if authorize_response.status_code != 302:
            raise OIDCFlowError(
                f"authorize should return 302, got {authorize_response.status_code}"
            )

        location = authorize_response.headers.get("Location", "")
        if not location:
            raise OIDCFlowError("authorize redirect is missing Location header")

        if config.login_path in location or config.authenticate_path in location:
            raise OIDCFlowError(
                "existing-session scenario reached login/authenticate unexpectedly"
            )

        final_redirect = _follow_redirect_chain_to_product(user, location, config)
        code = _extract_authorization_code(final_redirect, config.redirect_uri)
        _exchange_code_for_tokens(user, config, code)

    except Exception as exc:  # noqa: BLE001
        events.request.fire(
            request_type="FLOW",
            name=name,
            response_time=(perf_counter() - start) * 1000,
            response_length=0,
            exception=exc,
        )
        raise

    events.request.fire(
        request_type="FLOW",
        name=name,
        response_time=(perf_counter() - start) * 1000,
        response_length=0,
        exception=None,
    )
