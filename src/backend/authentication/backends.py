"""Accounts's custom backends for Python Social Auth"""

import json

import jwt
from jwt import (
    PyJWTError,
)
from social_core.backends.open_id_connect import OpenIdConnectAuth
from social_core.exceptions import AuthException, AuthTokenError

from core.utils.urls import add_query_params, get_query_params


class AuthACRNotAllowed(AuthException):
    """The identity provider authenticated the user with a non requested ACR."""

    def __init__(self, backend, acr, allowed_acr_values):
        super().__init__(backend, acr)
        self.acr = acr
        self.allowed_acr_values = allowed_acr_values

    def __str__(self):
        return (
            f"ACR not allowed: {self.acr!r}, "
            f"expected one of {' '.join(self.allowed_acr_values)}"
        )


class OpenIdConnectRPInitiatedLogoutMixin:
    """Mixin to support RP-initiated logout for ``OpenIdConnectAuth`` backends."""

    END_SESSION_URL = ""

    def end_session_url(self) -> str:
        """Return the base URL for RP-initiated logout"""

        return self.get_setting_config(
            "END_SESSION_URL", "end_session_endpoint", self.END_SESSION_URL
        )

    # pylint: disable=too-many-arguments
    def build_rp_initiated_logout_url(  # noqa: PLR0913
        self,
        *,
        id_token_hint=None,
        logout_hint=None,
        client_id=None,
        post_logout_redirect_uri=None,
        state=None,
        ui_locales=None,
    ):
        """Return the URL to call to initiate a logout from the RP"""
        return add_query_params(
            self.end_session_url(),
            {
                "id_token_hint": id_token_hint,
                "logout_hint": logout_hint,
                "client_id": client_id or self.setting("KEY"),
                "post_logout_redirect_uri": post_logout_redirect_uri,
                "state": state,
                "ui_locales": ui_locales,
            },
        )


class ProConnect(OpenIdConnectRPInitiatedLogoutMixin, OpenIdConnectAuth):
    """A ProConnect backend, based on OpenIdConnectAuth which handle user info as JWT"""

    name = "pro-connect"

    # ProConnect split the `profile` scope into 2: `given_name` and `usual_name`
    DEFAULT_SCOPE = ["openid", "email", "given_name", "usual_name", "siret"]
    FIRST_NAME_KEY = "given_name"
    LAST_NAME_KEY = "usual_name"

    EXTRA_DATA = [
        "id_token",
        "refresh_token",
        "sub",
        "email",
        "email_verified",
        "given_name",
        "usual_name",
        "siret",
        "roles",
    ]

    def login_hint(self) -> str | None:
        """Return the `login_hint` sent to the login view or to the `next` URL.

        The OIDC provider redirects unauthenticated users to the login view with
        the `/authorize` URL as `next`, so the client's `login_hint` is nested there.
        """
        if login_hint := self.data.get("login_hint"):
            return login_hint
        login_hint = get_query_params(self.data.get("next") or "").get("login_hint")
        return login_hint or None

    def mfa_required(self) -> bool:
        """Return whether users must be authenticated with an MFA ACR."""
        return bool(self.setting("MFA_REQUIRED", False))

    def acr_values(self) -> list[str]:
        """Return the ACR values requested to the identity provider."""
        setting = "MFA_ACR_VALUES" if self.mfa_required() else "ACR_VALUES"
        return (self.setting(setting) or "").split()

    def auth_params(self, state=None):
        params = super().auth_params(state)
        if login_hint := self.login_hint():
            params.setdefault("login_hint", login_hint)
        if acr_values := self.acr_values():
            params["acr_values"] = " ".join(acr_values)
            claims = json.loads(params.get("claims") or "{}")
            claims.setdefault("id_token", {})
            claims["id_token"].setdefault(
                "acr",
                {
                    "essential": self.mfa_required(),
                    "values": acr_values,
                },
            )
            params["claims"] = json.dumps(claims)
        return params

    def validate_claims(self, id_token) -> None:
        """Also reject ID tokens without an MFA `acr` when MFA is required.
        """
        super().validate_claims(id_token)
        if not self.mfa_required():
            return
        acr_values = self.acr_values()
        if id_token.get("acr") not in acr_values:
            raise AuthACRNotAllowed(self, id_token.get("acr"), acr_values)

    def user_data(self, access_token: str, *args, **kwargs):
        """Decode the JWT returned by ProConnect as user info"""

        user_info_jwt = self.request(
            self.userinfo_url(),
            headers={"Authorization": f"Bearer {access_token}"},
        ).content.decode("utf-8")

        key = self.find_valid_key(user_info_jwt)
        if not key:
            raise AuthTokenError(self, "Signature verification failed")

        try:
            user_info = jwt.decode(
                user_info_jwt,
                jwt.PyJWK(key).key,
                algorithms=self.setting("JWT_ALGORITHMS", self.JWT_ALGORITHMS),
                audience=self.get_key_and_secret()[0],
                issuer=self.id_token_issuer(),
            )
        except PyJWTError as error:
            raise AuthTokenError(self, str(error)) from error

        return self.validate_userinfo_sub(user_info)

    def extra_data(self, user, uid, response, details, pipeline_kwargs):
        data = super().extra_data(user, uid, response, details, pipeline_kwargs)
        # ProConnect nests `email_verified` in the `custom` claim, only returned
        # with the `custom` scope. Token refresh responses carry no `custom`
        # claim, the stored value is kept then.
        if isinstance(custom := response.get("custom"), dict):
            data["email_verified"] = custom.get("email_verified")
        return data

    def get_user_details(self, response):
        data = super().get_user_details(response)
        return {
            "sub": response["sub"],
            "email": data["email"],
            "short_name": data["first_name"] or "",
            "full_name": " ".join(
                [data["first_name"] or "", data["last_name"] or ""]
            ).strip(),
        }
