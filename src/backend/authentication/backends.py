import jwt
from jwt import (
    PyJWTError,
)
from social_core.backends.open_id_connect import OpenIdConnectAuth
from social_core.exceptions import AuthTokenError


class ProConnect(OpenIdConnectAuth):
    name = "pro-connect"

    # ProConnect split the `profile` scope into 2: `given_name` and `usual_name`
    SCOPE = ["given_name", "usual_name"]
    LAST_NAME_KEY = "usual_name"

    USER_FIELDS = [
        "username",
        "email",
        "sub",
        "fullname",
        "short_name",
    ]

    # def request(self, *args, **kwargs) -> Response:
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
            # {'sub': 'accounts@accounts.world', 'aud': 'accounts', 'email_verified': False, 'name': 'John Doe',
            #  'iss': 'http://localhost:9903/realms/accounts', 'last_name': 'Doe', 'preferred_username': 'accounts',
            #  'first_name': 'John', 'email': 'accounts@accounts.world'}
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
        # {'username': 'accounts', 'email': 'accounts@accounts.world', 'fullname': 'John Doe', 'first_name': None, 'last_name': None}
        data = super().get_user_details(response)
        data["full_name"] = data.pop("fullname")
        return data
