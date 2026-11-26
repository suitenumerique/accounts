"""Tests for Python Social Auth backends."""

import json
import uuid
from typing import cast

import jwt
import responses
from social_core.tests.backends import open_id_connect
from social_core.tests.backends.oauth import BaseAuthUrlTestMixin
from social_core.utils import get_querystring, parse_qs

from core.utils.urls import get_query_params

from authentication.backends import AuthACRNotAllowed


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
            "end_session_endpoint": f"{issuer}/logout",
        }
    )

    def setUp(self) -> None:
        super().setUp()

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

        self.id_token_acr = None

        # Clear the backend cache
        self.backend.oidc_config.invalidate()
        self.backend.get_jwks_keys.invalidate()

    def get_id_token(self, *args, **kwargs):
        id_token = super().get_id_token(*args, **kwargs)
        if self.id_token_acr is not None:
            id_token["acr"] = self.id_token_acr
        return id_token

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
        self.assertEqual(
            self.backend.end_session_url(), "https://pro.connect.fr/logout"
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

    def test_build_rp_initiated_logout_url(self) -> None:
        """Test the RP-initiated logout URL construction"""

        # Without any arguments
        self.assertEqual(
            self.backend.build_rp_initiated_logout_url(),
            f"https://pro.connect.fr/logout?client_id={self.client_key}",
        )
        # With all arguments
        params = {
            "id_token_hint": "id_token_hint",
            "logout_hint": "logout_hint",
            "client_id": "client_id",
            "post_logout_redirect_uri": "post_logout_redirect_uri",
            "state": "state",
            "ui_locales": "ui_locales",
        }
        self.assertDictEqual(
            get_query_params(self.backend.build_rp_initiated_logout_url(**params)),
            params,
        )

    def test_roles_scope_not_requested_by_default(self):
        """Test the `roles` scope is only requested when added to SCOPE"""
        self.assertEqual(
            self.backend.get_scope(),
            ["openid", "email", "given_name", "usual_name", "siret"],
        )

        self.strategy.set_settings(
            {**self.extra_settings(), f"SOCIAL_AUTH_{self.name}_SCOPE": ["roles"]}
        )
        self.assertEqual(
            self.backend.get_scope(),
            ["roles", "openid", "email", "given_name", "usual_name", "siret"],
        )

    def test_login_hint_auth_params(self):
        """Test the `login_hint` is forwarded, also when nested in the `next` URL"""
        self.assertNotIn("login_hint", self.backend.auth_params())

        self.strategy.set_request_data(
            {
                "next": "/api/v1.0/o/authorize/?client_id=abc&login_hint=next%40example.com"
            },
            self.backend,
        )
        self.assertEqual(self.backend.auth_params()["login_hint"], "next@example.com")

        self.strategy.set_request_data(
            {"login_hint": "direct@example.com"}, self.backend
        )
        self.assertEqual(self.backend.auth_params()["login_hint"], "direct@example.com")

    def set_acr_settings(self, **acr_settings):
        """Configure the ACR related settings of the backend."""
        self.strategy.set_settings(
            {
                **self.extra_settings(),
                **{
                    f"SOCIAL_AUTH_{self.name}_{name}": value
                    for name, value in acr_settings.items()
                },
            }
        )

    def test_acr_values_auth_params(self):
        """Test ACR_VALUES are requested as a voluntary claim without MFA"""
        self.set_acr_settings(ACR_VALUES="acr1 acr2", MFA_ACR_VALUES="mfa1 mfa2")

        params = self.backend.auth_params()
        self.assertEqual(params["acr_values"], "acr1 acr2")
        self.assertEqual(
            params["claims"],
            json.dumps(
                {"id_token": {"acr": {"essential": False, "values": ["acr1", "acr2"]}}}
            ),
        )

    def test_mfa_acr_values_auth_params(self):
        """Test MFA_ACR_VALUES are requested as an essential claim with MFA"""
        self.set_acr_settings(
            MFA_REQUIRED=True, ACR_VALUES="acr1 acr2", MFA_ACR_VALUES="mfa1 mfa2"
        )

        params = self.backend.auth_params()
        self.assertEqual(params["acr_values"], "mfa1 mfa2")
        self.assertEqual(
            params["claims"],
            json.dumps(
                {"id_token": {"acr": {"essential": True, "values": ["mfa1", "mfa2"]}}}
            ),
        )

    def test_mfa_acr_accepted(self):
        """Test the login succeeds with MFA when the ID token `acr` is an MFA one"""
        self.set_acr_settings(MFA_REQUIRED=True, MFA_ACR_VALUES="eidas1-mfa eidas2")
        self.id_token_acr = "eidas2"

        self.do_login()

    def test_mfa_acr_not_requested_rejected(self):
        """Test the login fails with MFA when the ID token `acr` is not an MFA one"""
        self.set_acr_settings(MFA_REQUIRED=True, MFA_ACR_VALUES="eidas1-mfa eidas2")
        self.id_token_acr = "eidas1"

        with self.assertRaisesRegex(
            AuthACRNotAllowed,
            "ACR not allowed: 'eidas1', expected one of eidas1-mfa eidas2",
        ):
            self.do_login()

    def test_mfa_acr_missing_rejected(self):
        """Test the login fails with MFA when the ID token has no `acr`"""
        self.set_acr_settings(MFA_REQUIRED=True, MFA_ACR_VALUES="eidas1-mfa eidas2")

        with self.assertRaisesRegex(
            AuthACRNotAllowed,
            "ACR not allowed: None, expected one of eidas1-mfa eidas2",
        ):
            self.do_login()

    def test_acr_not_checked_without_mfa(self):
        """Test any `acr` is accepted when MFA is not required"""
        self.set_acr_settings(ACR_VALUES="eidas1-mfa", MFA_ACR_VALUES="eidas1-mfa")
        self.id_token_acr = "eidas1"

        self.do_login()
