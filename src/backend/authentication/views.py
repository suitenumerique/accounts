"""Authentication views"""

from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import login_not_required
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect

from . import backends


@method_decorator([login_not_required, csrf_protect, never_cache], name="dispatch")
class LoginRoutingView(View):
    """
    Base routing view: when user needs to login, this page will redirect the user,
    based on their email on one of the identity provider available for them.
    """

    def get(self, request, *args, **kwargs):
        """First implementation is just a redirect to the only configured IdP (ProConnect)."""
        query = {}
        if redirect_value := request.GET.get(REDIRECT_FIELD_NAME, ""):
            # We don't validate the URL here because python-social-auth is configured to do it
            query[REDIRECT_FIELD_NAME] = redirect_value

        return HttpResponseRedirect(
            reverse(
                "authentication:social:begin",
                kwargs={"backend": backends.ProConnect.name},
                query=query,
            )
        )
