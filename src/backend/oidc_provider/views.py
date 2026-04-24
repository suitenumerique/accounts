"""Views for OIDC provider."""

import calendar
import hashlib

from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from oauth2_provider.compat import login_not_required
from oauth2_provider.models import get_access_token_model
from oauth2_provider.settings import oauth2_settings
from oauth2_provider.views import ClientProtectedScopedResourceView


@method_decorator(csrf_exempt, name="dispatch")
@method_decorator(login_not_required, name="dispatch")
class IntrospectTokenView(ClientProtectedScopedResourceView):
    """
    Implements an endpoint for token introspection based
    on RFC 7662 https://rfc-editor.org/rfc/rfc7662.html

    Overrides the oauth2_provider IntrospectTokenView to adapt to our needs.

    To access this view the request must pass a OAuth2 Bearer Token
    which is allowed to access the scope `introspection`.
    """

    required_scopes = ["introspection"]

    def _get_issuer(self, request):
        """Retrieve the issuer for the token introspection endpoint."""
        return oauth2_settings.oidc_issuer(request)

    @staticmethod
    def get_token_response(issuer, token_value=None):
        """Build the response for the token introspection endpoint."""
        try:
            token_checksum = hashlib.sha256(token_value.encode("utf-8")).hexdigest()
            token = (
                get_access_token_model()
                .objects.select_related("user", "application")
                .get(token_checksum=token_checksum)
            )
        except ObjectDoesNotExist:
            return JsonResponse({"active": False}, status=200)

        if token.is_valid():
            data = {
                "iss": issuer,
                "active": True,
                "scope": token.scope,
                "exp": int(calendar.timegm(token.expires.timetuple())),
            }
            if token.application:
                data["client_id"] = token.application.client_id
            if token.user:
                data["sub"] = token.user.sub
                data["email"] = token.user.email

            return JsonResponse(data)

        return JsonResponse({"active": False}, status=200)

    def get(self, request, *args, **kwargs):
        """
        Get the token from the URL parameters.
        URL: https://example.com/introspect?token=mF_9.B5f-4.1JqM

        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        issuer = self._get_issuer(request)
        return self.get_token_response(issuer, request.GET.get("token", None))

    def post(self, request, *args, **kwargs):
        """
        Get the token from the body form parameters.
        Body: token=mF_9.B5f-4.1JqM

        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        issuer = self._get_issuer(request)
        return self.get_token_response(issuer, request.POST.get("token", None))
