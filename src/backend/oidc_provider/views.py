"""Views for OIDC provider."""

from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from oauth2_provider.compat import login_not_required
from oauth2_provider.models import (
    AccessToken,
    RefreshToken,
    get_access_token_model,
    get_refresh_token_model,
)
from oauth2_provider.settings import oauth2_settings
from oauth2_provider.views import ClientProtectedScopedResourceView


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

        match request.POST.get("token_hint", "access_token"):
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

        for func in token_response_functions:
            response = func(token)
            if response:
                return response

        return self.INACTIVE_RESPONSE
