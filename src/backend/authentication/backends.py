import jwt
from jwt import (
    PyJWTError,
)
from social_core.backends.open_id_connect import OpenIdConnectAuth
from social_core.exceptions import AuthTokenError


class ProConnect(OpenIdConnectAuth):
    name = "pro-connect"

    # ProConnect split the `profile` scope into 2: `given_name` and `usual_name`
    DEFAULT_SCOPE = ["openid", "email", "given_name", "usual_name"]
    FIRST_NAME_KEY = "given_name"
    LAST_NAME_KEY = "usual_name"

    # def request(self, *args, **kwargs):
    #     response = super().request(*args, **kwargs)
    #     print("REQUEST - response", response, response.url, response.content)
    #     return response

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
            "username": data["username"],
            "email": data["email"],
            "short_name": data["first_name"],
            "full_name": " ".join([data["first_name"], data["last_name"]]),
        }
