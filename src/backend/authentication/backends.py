"""Accounts's custom backends for Python Social Auth"""

import jwt
from jwt import (
    PyJWTError,
)
from social_core.backends.open_id_connect import OpenIdConnectAuth
from social_core.exceptions import AuthTokenError


class ProConnect(OpenIdConnectAuth):
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
        "given_name",
        "usual_name",
        "siret",
    ]

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
