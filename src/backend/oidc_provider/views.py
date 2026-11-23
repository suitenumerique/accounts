"""Views for OIDC provider."""

import json
import logging
from collections import Counter
from typing import Any, NamedTuple

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.validators import validate_email
from django.db import IntegrityError
from django.http import JsonResponse
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

import requests
import social_django.utils
from oauth2_provider.compat import login_not_required
from oauth2_provider.exceptions import InvalidIDTokenError, OIDCError
from oauth2_provider.http import OAuth2ResponseRedirect
from oauth2_provider.models import (
    AccessToken,
    Application,
    RefreshToken,
    get_access_token_model,
    get_refresh_token_model,
)
from oauth2_provider.settings import oauth2_settings
from oauth2_provider.views import (
    ClientProtectedScopedResourceView,
)
from oauth2_provider.views import (
    RPInitiatedLogoutView as OAuth2RPInitiatedLogoutView,
)
from oauth2_provider.views.mixins import OAuthLibMixin
from oauthlib.common import Request as OauthlibRequest

from core.utils.state import set_state
from core.utils.urls import add_query_params

from authentication.models import IdentityProviderUser
from oidc_provider.models import ApplicationPolicy
from users.imports import match_or_create_product_users

logger = logging.getLogger(__name__)


@method_decorator([csrf_exempt], "dispatch")
class RPInitiatedLogoutView(OAuth2RPInitiatedLogoutView):
    """
    Override the default RP-Initiated Logout endpoint behavior.
    https://openid.net/specs/openid-connect-rpinitiated-1_0.html

    We redirect to frontend URLs instead of internal URLs,
    for now errors are still displayed by the backend.
    """

    def get(self, request, *args, **kwargs):
        """Handle GET request, as required by the RFC"""

        return self.relying_party_initiated_logout(request.GET)

    def post(self, request, *args, **kwargs):
        """Handle POST request, unlike oauth2_provider, as required by the RFC"""

        return self.relying_party_initiated_logout(request.POST)

    def relying_party_initiated_logout(self, request_data):
        """Override oauth2_provider behavior to handle everything in our logout endpoint"""
        id_token_hint = request_data.get("id_token_hint")
        client_id = request_data.get("client_id")
        post_logout_redirect_uri = request_data.get("post_logout_redirect_uri")
        state = request_data.get("state")

        state_data = {}
        try:
            application, token_user = self.validate_logout_request(
                id_token_hint=id_token_hint,
                client_id=client_id,
                post_logout_redirect_uri=post_logout_redirect_uri,
            )
        except InvalidIDTokenError as error:
            # Don't break, but still log, on invalid id_token, the specifications
            # allow to continue the logout process as long as we prompt the user about it.
            logger.exception(error.description)
            prompt = "consent"
            allowed_schemes = oauth2_settings.ALLOWED_REDIRECT_URI_SCHEMES
            if post_logout_redirect_uri:
                # XXX(rsebille): We probably should ignore the `post_logout_redirect_uri` in this
                # case as we can't *properly* validate it, but we also don't want to prevent
                # users to log out and create an error because of an unknown token.
                for application in Application.objects.all():
                    if application.post_logout_redirect_uri_allowed(
                        post_logout_redirect_uri
                    ):
                        break
                else:
                    # The URI doesn't match any of the configured application so
                    # ignore it to prevent an open redirect vulnerability.
                    post_logout_redirect_uri = None
        except OIDCError as error:
            return self.error_response(error)
        else:
            prompt = "none" if not self.must_prompt(token_user) else "consent"
            allowed_schemes = application.get_allowed_schemes()

        # Build final post_logout_redirect_uri
        if post_logout_redirect_uri:
            if state:
                post_logout_redirect_uri = add_query_params(
                    post_logout_redirect_uri, {"state": state}
                )
            response = OAuth2ResponseRedirect(post_logout_redirect_uri, allowed_schemes)
            if not self.request.user.is_authenticated and prompt == "none":
                return response
            state_data["post_logout_redirect_uri"] = response.url

        state_key = set_state(self.request.session, data=state_data)
        return OAuth2ResponseRedirect(
            self.request.build_absolute_uri(
                reverse(
                    "authentication:logout",
                    query={"state": state_key, "prompt": prompt},
                )
            ),
            allowed_schemes,
        )


@method_decorator(csrf_exempt, name="dispatch")
@method_decorator(login_not_required, name="dispatch")
class IntrospectTokenView(ClientProtectedScopedResourceView):
    """
    Implements an endpoint for token introspection based
    on RFC 7662 https://rfc-editor.org/rfc/rfc7662.html

    The oauth2_provider's IntrospectTokenView doesn't
    follow the specs so we try to do better.

    To access this view the request must pass a
    OAuth2 Bearer Token with the scope `introspection`.
    """

    required_scopes = ["introspection"]
    INACTIVE_RESPONSE = JsonResponse({"active": False})

    def _get_access_token_response(self, token_value):
        try:
            token: AccessToken = (
                get_access_token_model()
                .objects.select_related("user", "application")
                .get(token=token_value)
            )
        except ObjectDoesNotExist:
            return None

        if token.is_valid():
            return JsonResponse(
                {
                    "active": True,
                    "scope": token.scope,
                    "client_id": token.application.client_id,
                    "username": token.user.get_username(),
                    "exp": int(token.expires.timestamp()),
                    "iat": int(token.created.timestamp()),
                    "sub": token.user.sub,
                    "aud": token.application.client_id,
                    "iss": oauth2_settings.oidc_issuer(self.request),
                }
            )
        return self.INACTIVE_RESPONSE

    def _get_refresh_token_response(self, token_value):
        try:
            token: RefreshToken = (
                get_refresh_token_model()
                .objects.select_related("user", "application", "access_token")
                .get(token=token_value)
            )
        except ObjectDoesNotExist:
            return None

        if not token.revoked:
            return JsonResponse(
                {
                    "active": True,
                    "scope": token.access_token.scope,
                    "client_id": token.application.client_id,
                    "username": token.user.get_username(),
                    # No "exp" as the default oauth2_provider RefreshToken doesn't expire
                    "iat": int(token.created.timestamp()),
                    "sub": token.user.sub,
                    "aud": token.application.client_id,
                    "iss": oauth2_settings.oidc_issuer(self.request),
                }
            )
        return self.INACTIVE_RESPONSE

    def _get_psa_backend_fallback_response(self, token_value):
        for backend_name in settings.OAUTH2_PROVIDER_INTROSPECTION_PSA_BACKEND_FALLBACK:
            backend = social_django.utils.load_strategy(self.request).get_backend(
                backend_name
            )
            introspection_url = backend.get_setting_config(
                "INTROSPECTION_URL", "introspection_endpoint", ""
            )
            if not introspection_url:
                continue

            client_id, client_secret = backend.get_key_and_secret()
            response = requests.post(
                introspection_url,
                data={
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "token": token_value,
                },
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Accept": "application/json",
                },
                timeout=5,
            )
            try:
                response.raise_for_status()
            except requests.HTTPError:
                continue
            else:
                introspection_response = response.json()
                if introspection_response.get("active") is not True:
                    return self.INACTIVE_RESPONSE

                # Copy some values as is:
                #  - `active` will should be true
                #  - `client_id` and `aud` can be used to limit access or permissions
                rewritten_response = {
                    k: v
                    for k, v in introspection_response.items()
                    if k in {"active", "client_id", "aud"}
                }
                # Translate the backend's sub to the accounts' sub. When the user never
                # logged in through accounts, resource servers may still know them by the
                # backend's sub, so forward it as is rather than leaving them unidentified.
                if subject := introspection_response.get("sub"):
                    if social_auth := IdentityProviderUser.get_social_auth(
                        provider=backend.name, uid=subject
                    ):
                        rewritten_response["sub"] = social_auth.user.sub
                    else:
                        # Do not log the sub: it identifies a person.
                        logger.warning(
                            "No accounts user mapped to this %s identity, "
                            "forwarding its sub on token introspection",
                            backend.name,
                        )
                        rewritten_response["sub"] = subject
                # Limit which scope are forwarded as is, we don't necessarily have the same ones
                if scope := introspection_response.get("scope"):
                    rewritten_response["scope"] = " ".join(
                        s
                        for s in scope.split(" ")
                        if s
                        in settings.OAUTH2_PROVIDER_INTROSPECTION_PSA_BACKEND_FALLBACK_PASSTHROUGH_SCOPES  # pylint: disable=line-too-long
                    )
                return JsonResponse(rewritten_response)

        return None

    def post(self, request, *args, **kwargs):
        """
        Get the token from the body form parameters.
        Body: token=mF_9.B5f-4.1JqM

        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        token = request.POST.get("token")
        if not token:
            # The specifications are not particularly explicit on this one,
            # but it seems to favor returning an inactive response for
            # every error except the authorization one's.
            return self.INACTIVE_RESPONSE

        match request.POST.get("token_type_hint", "access_token"):
            case "access_token":
                token_response_functions = [
                    self._get_access_token_response,
                    self._get_refresh_token_response,
                ]
            case "refresh_token":
                token_response_functions = [
                    self._get_refresh_token_response,
                    self._get_access_token_response,
                ]
            case _:
                return self.INACTIVE_RESPONSE

        if settings.OAUTH2_PROVIDER_INTROSPECTION_PSA_BACKEND_FALLBACK:
            token_response_functions.append(self._get_psa_backend_fallback_response)

        for func in token_response_functions:
            response = func(token)
            if response:
                return response

        return self.INACTIVE_RESPONSE


class CleanedRow(NamedTuple):
    """A row of a users import, with a sub and an email only when it is valid."""

    pk: Any
    sub: str | None = None
    email: str | None = None


@method_decorator(csrf_exempt, name="dispatch")
@method_decorator(login_not_required, name="dispatch")
class UsersImportView(OAuthLibMixin, View):
    """
    Match the users of a product with accounts users, creating the unknown ones.

    Products call this endpoint by batches to replace the identity provider's
    subs of their users by accounts subs. See `users.imports.match_or_create_product_users`.

    To access this view the request must pass the client credentials with
    HTTP Basic authentication, and the policy of the client must allow it to
    import users. A Bearer token is not enough: users must not be created on
    behalf of another user.

    Body (JSON):
        {"users": [{"pk": "...", "sub": "...", "email": "..."}]}

    `dry_run` is optional: `true` reports what would be created, without writing.
    `pk` is the product's own identifier, returned as is. A row without a
    valid `sub` or `email` is returned with the `invalid` status.
    """

    http_method_names = ["post", "options"]
    INVALID_STATUS = "invalid"

    @staticmethod
    def _error_response(error, description, status=400):
        return JsonResponse(
            {"error": error, "error_description": description}, status=status
        )

    def _get_client(self, request):
        """Return the client authenticated by its credentials, None otherwise.

        Same as OAuthLibCore.authenticate_client, which only returns a boolean:
        the client is needed for its policy.
        """
        core = self.get_oauthlib_core()
        # pylint: disable=protected-access
        uri, http_method, body, headers = core._extract_params(request)  # noqa: SLF001
        oauth_request = OauthlibRequest(uri, http_method, body, headers)
        if not core.server.request_validator.authenticate_client(oauth_request):
            return None
        return oauth_request.client

    @staticmethod
    def _clean_row(row):
        """Return the pk of a row, with its sub and email only when they are valid."""
        if not isinstance(row, dict):
            return CleanedRow(pk=None)
        pk, sub, email = row.get("pk"), row.get("sub"), row.get("email")
        if not isinstance(sub, str) or not 0 < len(sub) <= 255:
            return CleanedRow(pk)
        if not isinstance(email, str):
            return CleanedRow(pk)
        try:
            validate_email(email)
        except ValidationError:
            return CleanedRow(pk)
        return CleanedRow(pk, sub, email)

    def _client_error_response(self, client):
        """Return the error response when the client is refused, None otherwise."""
        if client is None:
            return self._error_response(
                "invalid_client", "Client authentication failed.", status=401
            )
        if not ApplicationPolicy.for_application(client).import_users:
            return self._error_response(
                "unauthorized_client",
                "This client is not allowed to import users.",
                status=403,
            )
        return None

    @staticmethod
    def _parse_body(body):
        """Return the rows, the dry run flag and an error description, if any."""
        try:
            payload = json.loads(body)
        except ValueError:
            return None, None, "The body must be JSON."
        rows = payload.get("users") if isinstance(payload, dict) else None
        if not isinstance(rows, list):
            return None, None, "The users parameter must be a list."
        dry_run = payload.get("dry_run", False)
        if not isinstance(dry_run, bool):
            return None, None, "The dry_run parameter must be a boolean."
        return rows, dry_run, None

    def _build_results(self, cleaned_rows, results_by_sub):
        """Return the result of each row, in the order of the rows."""
        results = []
        for cleaned_row in cleaned_rows:
            result = results_by_sub[cleaned_row.sub] if cleaned_row.sub else None
            results.append(
                {
                    "pk": cleaned_row.pk,
                    "sub": cleaned_row.sub,
                    "status": result.status if result else self.INVALID_STATUS,
                    "accounts_sub": result.accounts_sub if result else None,
                }
            )
        return results

    def post(self, request, *args, **kwargs):
        """Authenticate the client and return one result per user of the batch."""
        # A multipart body is consumed by the client authentication, and
        # request.body cannot be read afterwards. Read it first so an invalid
        # body is a 400.
        body = request.body
        client = self._get_client(request)
        if error_response := self._client_error_response(client):
            return error_response
        application = (
            f"{client.name} ({client.client_id})" if client.name else client.client_id
        )
        rows, dry_run, error = self._parse_body(body)
        if error:
            logger.warning(
                "Invalid users import request body from %s: %s", application, error
            )
            return self._error_response("invalid_request", error)

        cleaned_rows = [self._clean_row(row) for row in rows]
        # accounts matches and creates the users by sub: several rows with the
        # same sub are the same person, and get the same result. Only the email
        # of the first one is used, to create the user.
        emails_by_sub = {}
        for cleaned_row in cleaned_rows:
            if cleaned_row.sub:
                emails_by_sub.setdefault(cleaned_row.sub, cleaned_row.email)
        try:
            results_by_sub = match_or_create_product_users(
                emails_by_sub, dry_run=dry_run
            )
        except IntegrityError:
            # A concurrent import created some of these users first.
            return self._error_response(
                "conflict", "Concurrent import, retry the request.", status=409
            )

        results = self._build_results(cleaned_rows, results_by_sub)
        counts = Counter(result["status"] for result in results)
        logger.info(
            "Users import by %s%s: %s",
            application,
            " (dry run)" if dry_run else "",
            dict(counts),
        )
        return JsonResponse({"counts": counts, "results": results})
