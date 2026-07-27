"""Accounts's custom backends for Python Social Auth"""

import secrets

from django.contrib.auth.backends import ModelBackend

import jwt
from asgiref.sync import sync_to_async
from jwt import PyJWTError
from social_core.backends.open_id_connect import OpenIdConnectAuth
from social_core.exceptions import AuthTokenError

from core.standards import rfc7636

from authentication import models


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
        "email_verified",
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


class AuthRequestBackend(ModelBackend):
    """Authenticate against ``AuthRequestAttempt`` and settings.AUTH_USER_MODEL"""

    def authenticate(
        self,
        request,
        auth_request_attempt: models.AuthRequestAttempt,
        secret: str,
        client_verifier: str,
        **kwargs,
    ):  # pylint: disable=arguments-differ
        """Authenticate a user using an ``AuthRequestAttempt``.

        Failing the code challenge or secrets comparaison doesn't currently invalidate the
        authentication request attempt, this could be done but for now this seems to have
        more drawbacks than the alternative:
         - this will make handling password failures a lot more complicated
         - a legitimate user could be prevented to log in, voluntarily or involuntarily
         - the (relatively) short expiration timestamp and the two UUID primary keys heavily
           reduce brute force opportunities, especially combined with a rate limit.
        """
        is_active = (
            auth_request_attempt.is_active()
            and auth_request_attempt.request.is_active()
        )

        # First, check the client challenge match the client verifier
        code_challenge_verified = rfc7636.verify_code_verifier(
            client_verifier, auth_request_attempt.client_challenge
        )

        # Then, check the user is present and can authenticate
        try:
            user = auth_request_attempt.request.user
        except AttributeError:
            user = None
            user_can_authenticate = False
        else:
            user_can_authenticate = self.user_can_authenticate(user)

        # Finally, check the given secret match the one we know
        match auth_request_attempt.strategy:
            case models.AuthRequestStrategy.PASSWORD:
                # The PASSWORD strategy's secret is the raw password so if we need a special case
                # it's better to call AbstractBaseUser.check_password() and let Django handling
                # everything, like the hash regeneration/hardening, than doing it ourselves.
                secret_verified = user and user.check_password(secret)
            case _:
                secret_verified = secrets.compare_digest(
                    secret, auth_request_attempt.secret
                )

        if not all(
            [is_active, code_challenge_verified, user_can_authenticate, secret_verified]
        ):
            return None

        # Everything is in order, mark the authentication request attempt as fulfilled
        auth_request_attempt.fulfill()
        # And return the authenticated user
        return user

    async def aauthenticate(self, request, **kwargs):  # pylint: disable=arguments-differ
        """See authenticate()."""
        return await sync_to_async(self.authenticate)(request, **kwargs)
