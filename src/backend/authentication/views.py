"""Authentication views"""

from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME, get_user_model
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_not_required
from django.contrib.auth.views import RedirectURLMixin
from django.http import HttpResponseRedirect
from django.shortcuts import resolve_url
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect

User = get_user_model()


@method_decorator([login_not_required, csrf_protect, never_cache], name="dispatch")
class LoginRoutingView(View):
    """
    Base routing view: when user needs to login, this page will redirect the user,
    based on their email on one of the identity provider available for them.
    """

    def get(self, request, *args, **kwargs):
        """First implementation is just a redirect to the only configured IdP (ProConnect)."""

        return HttpResponseRedirect(
            reverse(
                "authentication:social:begin",
                kwargs={"backend": "pro-connect"},
                # We don't validate the URL here because PSA is configured to do it
                query={REDIRECT_FIELD_NAME: request.GET.get(REDIRECT_FIELD_NAME)},
            )
        )


@method_decorator([csrf_protect, never_cache], name="dispatch")
class LogoutView(RedirectURLMixin, View):
    http_method_names = ["post", "options"] + (
        ["get"] if settings.LOGOUT_URL_ALLOW_GET_METHOD else []
    )

    def get_default_redirect_url(self):
        if settings.LOGOUT_REDIRECT_URL:
            return resolve_url(settings.LOGOUT_REDIRECT_URL)
        return self.request.path

    def _do_logout(self, request):
        auth_logout(request)
        return HttpResponseRedirect(self.get_success_url())

    def get(self, request, *args, **kwargs):
        return self._do_logout(request)

    def post(self, request, *args, **kwargs):
        return self._do_logout(request)
