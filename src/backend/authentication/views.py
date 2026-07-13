"""Authentication views"""

from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import login_not_required
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect

import social_django.utils as social_utils
from social_core.actions import do_auth

from . import backends


@method_decorator([login_not_required, csrf_protect, never_cache], name="dispatch")
class LoginRoutingView(View):
    """
    Base routing view: when user needs to log in, this page will redirect the user,
    based on their email on one of the identity provider available for them.
    """

    def get(self, request, *args, **kwargs):
        """First implementation is just a redirect to the only configured IdP (ProConnect)."""
        backend = backends.ProConnect.name
        # The builtin view `social_django.views.auth` will become POST-only
        # so a `HttpResponseRedirect()` even with `preserve_request=True`
        # will not work as the CSRF token in the body will be the same...
        # We also need to maintain the GET method for this view otherwise
        # this break the redirection done by the OIDC Provider when the
        # client call `/authorize` and is not yet logged in.
        # Until we find a proper solution for that particulars problems we copy what is done
        # by `@social_django.utils.psa()` and `social_django.views.auth` to keep the routing
        # logic in one place and relatively simple.
        return do_auth(
            social_utils.load_backend(
                social_utils.load_strategy(request),
                backend,
                redirect_uri=reverse(
                    "authentication:social:complete", kwargs={"backend": backend}
                ),
            ),
            redirect_name=REDIRECT_FIELD_NAME,
        )
