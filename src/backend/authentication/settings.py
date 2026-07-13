"""Django settings dedicated to the authentication application."""

from configurations import values
from lasuite.configuration.values import SecretFileValue


class AuthenticationSettings:
    """Authentication settings: configure Django login and Python Social Auth."""

    LOGIN_URL = "authentication:login"
    LOGIN_REDIRECT_URL = values.Value(None, environ_prefix=None)
    LOGOUT_REDIRECT_URL = values.Value(None, environ_prefix=None)

    SOCIAL_AUTH_REQUIRE_POST = (
        False  # This will become the default in social-app-django>=6.0.0
    )

    SOCIAL_AUTH_SANITIZE_REDIRECTS = True
    SOCIAL_AUTH_ALLOWED_REDIRECT_HOSTS = values.ListValue([], environ_prefix=None)

    SOCIAL_AUTH_URL_NAMESPACE = "authentication:social"
    SOCIAL_AUTH_JSONFIELD_ENABLED = True

    SOCIAL_AUTH_USERNAME_IS_FULL_EMAIL = True  # Our User()'s username is an email
    SOCIAL_AUTH_FORCE_EMAIL_LOWERCASE = True

    SOCIAL_AUTH_STRATEGY = "authentication.social_auth.OptionalURLSettingStrategy"
    SOCIAL_AUTH_STORAGE = "authentication.social_auth.AccountsDjangoStorage"
    SOCIAL_AUTH_USER_FIELDS = ["email", "sub"]

    SOCIAL_AUTH_PIPELINE = (
        # Get the information we can about the user and return it in a simple
        # format to create the user instance later. In some cases the details are
        # already part of the auth response from the provider, but sometimes this
        # could hit a provider API.
        "social_core.pipeline.social_auth.social_details",
        # Get the social uid from whichever service we're authing thru. The uid is
        # the unique identifier of the given user in the provider.
        "social_core.pipeline.social_auth.social_uid",
        # Checks if the current social-account is already associated in the site.
        "social_core.pipeline.social_auth.social_user",
        # Make up a username for this person, appends a random string at the end if
        # there's any collision.
        "social_core.pipeline.user.get_username",
        # Associates the current social details with another user account with
        # a similar email address. Beware that could be a security issue if a
        # provider doesn't validate the email, as explained by the pipeline function.
        "social_core.pipeline.social_auth.associate_by_email",
        # Create a user account if we haven't found one yet.
        "social_core.pipeline.user.create_user",
        # Create the record that associates the social account with the user.
        "social_core.pipeline.social_auth.associate_user",
        # Populate the extra_data field in the social record with the values
        # specified by settings (and the default ones like access_token, etc).
        "social_core.pipeline.social_auth.load_extra_data",
        # Update the user record with any changed info from the auth service.
        "social_core.pipeline.user.user_details",
    )
    SOCIAL_AUTH_DISCONNECT_PIPELINE = (
        # Verifies that the social association can be disconnected from the current
        # user (ensure that the user login mechanism is not compromised by this
        # disconnection).
        "social_core.pipeline.disconnect.allowed_to_disconnect",
        # Collects the social associations to disconnect.
        "social_core.pipeline.disconnect.get_entries",
        # Revoke any access_token when possible.
        "social_core.pipeline.disconnect.revoke_tokens",
        # Removes the social associations.
        "social_core.pipeline.disconnect.disconnect",
    )

    # ProConnect backend
    SOCIAL_AUTH_PRO_CONNECT_KEY = values.Value(environ_prefix=None)
    SOCIAL_AUTH_PRO_CONNECT_SECRET = SecretFileValue(environ_prefix=None)

    SOCIAL_AUTH_PRO_CONNECT_OIDC_ENDPOINT = values.Value(environ_prefix=None)
    SOCIAL_AUTH_PRO_CONNECT_ID_TOKEN_ISSUER = values.Value(environ_prefix=None)
    SOCIAL_AUTH_PRO_CONNECT_ACCESS_TOKEN_URL = values.Value(environ_prefix=None)
    SOCIAL_AUTH_PRO_CONNECT_AUTHORIZATION_URL = values.Value(environ_prefix=None)
    SOCIAL_AUTH_PRO_CONNECT_REVOKE_TOKEN_URL = values.Value(environ_prefix=None)
    SOCIAL_AUTH_PRO_CONNECT_USERINFO_URL = values.Value(environ_prefix=None)
    SOCIAL_AUTH_PRO_CONNECT_JWKS_URI = values.Value(environ_prefix=None)
