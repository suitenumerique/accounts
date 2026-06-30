"""Tests for Python Social Auth backends."""

import json
import uuid
from typing import cast

import jwt
import responses
from social_core.tests.backends import open_id_connect
from social_core.tests.backends.oauth import BaseAuthUrlTestMixin
from social_core.utils import get_querystring, parse_qs


class ProConnectTest(open_id_connect.OpenIdConnectTest, BaseAuthUrlTestMixin):
    """Test the ProConnect backend with Python Social Auth testing utilities."""

    backend_path = "authentication.backends.ProConnect"
    issuer = "https://pro.connect.fr"
    client_key = str(uuid.uuid4())
    expected_username = "test@example.com"

    openid_config_body = json.dumps(
        {
            "issuer": issuer,
            "authorization_endpoint": f"{issuer}/authorize",
            "token_endpoint": f"{issuer}/token",
            "userinfo_endpoint": f"{issuer}/userinfo",
            "revocation_endpoint": f"{issuer}/token/revocation",
            "jwks_uri": f"{issuer}/jwks",
        }
    )

    def setUp(self) -> None:
        super().setUp()
        # Clear the backend's cached methods
        self.backend.oidc_config.invalidate()
        self.backend.get_jwks_keys.invalidate()

        self.user_data_content_type = "application/jwt"
        self.user_data_url = f"{self.issuer}/userinfo"
        self.user_data_body = jwt.encode(
            payload={
                "iss": self.issuer,
                "aud": self.client_key,
                "sub": self.expected_username,
                "email": "test@example.com",
                "email_verified": True,
                "given_name": "Test",
                "usual_name": "User",
            },
            key=jwt.PyJWK(self.key).key,
            algorithm="RS256",
        )

    def extra_settings(self):
        settings = super().extra_settings()
        settings.update(
            {
                "SOCIAL_AUTH_PRO_CONNECT_OIDC_ENDPOINT": self.issuer,
                # No username or prefered_username claims are returned by ProConnect, use the email.
                "SOCIAL_AUTH_USERNAME_IS_FULL_EMAIL": True,
            }
        )
        return settings

    def pre_complete_callback(self, start_url) -> None:
        self.access_token_kwargs.setdefault("subject", self.expected_username)
        super().pre_complete_callback(start_url)

    def test_domain_configuration(self) -> None:
        """Test that domain-based URLs are constructed correctly"""
        self.assertEqual(
            self.backend.authorization_url(), "https://pro.connect.fr/authorize"
        )
        self.assertEqual(
            self.backend.access_token_url(), "https://pro.connect.fr/token"
        )

    def test_pkce_can_be_enabled_by_setting(self) -> None:
        """Test the backend when USE_PKCE=True."""

        self.strategy.set_settings(
            {
                **self.extra_settings(),
                f"SOCIAL_AUTH_{self.name}_USE_PKCE": True,
            }
        )

        self.do_start()

        auth_request = next(
            r.request
            for r in responses.calls
            if cast("str", r.request.url).startswith(self.backend.authorization_url())
        )
        code_challenge = get_querystring(cast("str", auth_request.url)).get(
            "code_challenge"
        )
        code_challenge_method = get_querystring(cast("str", auth_request.url)).get(
            "code_challenge_method"
        )

        self.assertIsNotNone(code_challenge)
        self.assertEqual(code_challenge_method, "S256")

        auth_complete = next(
            r.request
            for r in responses.calls
            if cast("str", r.request.url).startswith(self.backend.access_token_url())
        )
        code_verifier = parse_qs(auth_complete.body).get("code_verifier")

        self.assertEqual(
            self.backend.generate_code_challenge(code_verifier, code_challenge_method),
            code_challenge,
        )

    def test_everything_works(self) -> None:
        """Test a complete login."""
        self.do_login()
