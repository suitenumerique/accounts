"""Authentication views"""

from urllib.parse import quote_plus

from django.contrib.auth import get_user_model
from django.http import HttpResponseRedirect
from django.views import View

User = get_user_model()


class LoginRoutingView(View):
    """
    Base routing view: when user needs to login, this page will redirect the user,
    based on their email on one of the identity provider available for them.
    """

    http_method_names = ["get"]

    def get(self, request, *args, **kwargs):
        """First implementation is just a redirect to the only configured IdP (OIDC)."""
        _next = request.GET.get("next")

        # Build the redirect URL with the next parameter if present
        if _next:
            # Properly encode the next parameter to prevent issues with special characters
            encoded_next = quote_plus(_next)
            redirect_url = f"/oidc/authenticate/?next={encoded_next}"
        else:
            redirect_url = "/oidc/authenticate/"

        return HttpResponseRedirect(redirect_url)
