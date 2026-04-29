"""Configuration helpers for OIDC load tests."""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
# pylint: disable=too-many-instance-attributes
class OIDCLoadTestConfig:
    """Runtime configuration loaded from environment variables."""

    authorize_path: str = os.getenv("OIDC_LOADTEST_AUTHORIZE_PATH", "/api/v1.0/o/authorize/")
    login_path: str = os.getenv("OIDC_LOADTEST_LOGIN_PATH", "/api/v1.0/login/")
    authenticate_path: str = os.getenv(
        "OIDC_LOADTEST_AUTHENTICATE_PATH", "/api/v1.0/oidc/authenticate/"
    )
    callback_path: str = os.getenv("OIDC_LOADTEST_CALLBACK_PATH", "/api/v1.0/oidc/callback/")
    token_path: str = os.getenv("OIDC_LOADTEST_TOKEN_PATH", "/api/v1.0/o/token/")
    client_id: str = os.getenv("OIDC_LOADTEST_CLIENT_ID", "oidc-test-client")
    client_secret: str = os.getenv("OIDC_LOADTEST_CLIENT_SECRET", "oidc-test-secret")
    redirect_uri: str = os.getenv(
        "OIDC_LOADTEST_REDIRECT_URI", "https://client.example.test/callback"
    )
    scope: str = os.getenv("OIDC_LOADTEST_SCOPE", "openid email")
    expected_upstream_issuer: str = os.getenv("OIDC_LOADTEST_EXPECTED_UPSTREAM_ISSUER", "")
    max_redirect_hops: int = int(os.getenv("OIDC_LOADTEST_MAX_REDIRECT_HOPS", "8"))
    # Nom du profil de charge piloté par `profiles.py`.
    profile: str = os.getenv("OIDC_LOADTEST_PROFILE", "manual")
    # Répartition des classes utilisateurs Locust pour simuler un trafic réel.
    existing_session_user_weight: int = int(
        os.getenv("OIDC_LOADTEST_EXISTING_SESSION_USER_WEIGHT", "70")
    )
    new_session_user_weight: int = int(
        os.getenv("OIDC_LOADTEST_NEW_SESSION_USER_WEIGHT", "30")
    )


CONFIG = OIDCLoadTestConfig()
