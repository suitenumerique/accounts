"""Views for OIDC provider."""

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie

import requests
import social_django.utils
from oauth2_provider.compat import login_not_required
from oauth2_provider.exceptions import OIDCError
from oauth2_provider.http import OAuth2ResponseRedirect
from oauth2_provider.models import (
    AccessToken,
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

from core.utils.state import set_state
from core.utils.urls import add_query_params

from authentication.models import IdentityProviderUser


@method_decorator([ensure_csrf_cookie], "dispatch")
class RPInitiatedLogoutView(OAuth2RPInitiatedLogoutView):
    """
    Override the default RP-Initiated Logout endpoint behavior.
    https://openid.net/specs/openid-connect-rpinitiated-1_0.html

    We redirect to frontend URLs instead of internal URLs,
    for now errors are still displayed by the backend.
    """

    def get(self, request, *args, **kwargs):
        """Override oauth2_provider behavior to handle everything in our logout endpoint"""

        id_token_hint = request.GET.get("id_token_hint")
        client_id = request.GET.get("client_id")
        post_logout_redirect_uri = request.GET.get("post_logout_redirect_uri")
        state = request.GET.get("state")

        try:
            application, token_user = self.validate_logout_request(
                id_token_hint=id_token_hint,
                client_id=client_id,
                post_logout_redirect_uri=post_logout_redirect_uri,
            )
        except OIDCError as error:
            return self.error_response(error)

        state_data = {}
        # Build final post_logout_redirect_uri
        if post_logout_redirect_uri:
            if state:
                post_logout_redirect_uri = add_query_params(
                    post_logout_redirect_uri, {"state": state}
                )
            response = OAuth2ResponseRedirect(
                post_logout_redirect_uri, application.get_allowed_schemes()
            )
            if not request.user.is_authenticated:
                return response
            state_data["post_logout_redirect_uri"] = response.url

        state_key = set_state(request.session, data=state_data)
        prompt = "none" if not self.must_prompt(token_user) else "consent"
        return OAuth2ResponseRedirect(
            request.build_absolute_uri(
                reverse(
                    "authentication:logout",
                    query={"state": state_key, "prompt": prompt},
                )
            ),
            application.get_allowed_schemes(),
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
                # Translate the backend's sub to the accounts' sub
                if subject := introspection_response.get("sub"):
                    if social_auth := IdentityProviderUser.get_social_auth(
                        provider=backend.name, uid=subject
                    ):
                        rewritten_response["sub"] = social_auth.user.sub
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
