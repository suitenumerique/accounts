"""Authentication views"""

from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_not_required, login_required
from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect

import social_django
import social_django.utils as social_utils
from oauth2_provider.models import (
    get_access_token_model,
    get_application_model,
    get_refresh_token_model,
)
from oauth2_provider.settings import oauth2_settings
from social_core.actions import do_auth

from core.utils.state import get_state, set_state, state_exists
from core.utils.urls import add_query_params

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


@method_decorator([login_required, csrf_protect, never_cache], name="dispatch")
class LogoutView(View):
    """Start the log-out process, eventually prompting them before redirecting them to an IdP."""

    http_method_names = ["get", "post", "options"]

    @staticmethod
    def _identity_provider_logout_url(request, state_key):
        idp_user = request.user.identity_providers.get()
        backend = social_django.utils.load_strategy(request).get_backend(
            idp_user.provider
        )
        return backend.build_rp_initiated_logout_url(
            id_token_hint=idp_user.extra_data.get("id_token"),
            post_logout_redirect_uri=request.build_absolute_uri(
                reverse("authentication:logout-end")
            ),
            state=state_key,
        )

    def get(self, request, *args, **kwargs):
        """Prompt the user if needed, otherwise redirect the user to an IdP to be logged out"""

        state_key = request.GET.get("state")
        if state_exists(request.session, state_key):
            # If we have a valid state then we are coming from a trusted source,
            # so we can skip prompting the user to streamline the process.
            prompt = request.GET.get("prompt", "none")
        else:
            prompt = "consent"
            state_key = None

        match prompt:
            case "none":
                redirect_to = self._identity_provider_logout_url(request, state_key)
            case "consent" | _:
                redirect_to = add_query_params(
                    settings.FRONTEND_LOGOUT_URL,
                    {"state": state_key},
                )

        return HttpResponseRedirect(redirect_to)

    def post(self, request, *args, **kwargs):
        """Redirect the user to an IdP to be logged out"""

        state_key = request.POST.get("state")
        if not state_exists(request.session, state_key):
            # When logging out through the frontend there will be no prepopulated state,
            # but since it's a POST and we use the CSRFMiddleware we can create it on the fly.
            state_key = set_state(request.session)

        return HttpResponseRedirect(
            self._identity_provider_logout_url(request, state_key)
        )


@method_decorator([login_required, csrf_protect, never_cache], name="dispatch")
class LogoutEndView(View):
    """End the log-out process for a user, possibly revoking its tokens"""

    http_method_names = ["get", "options"]

    def oauth2_provider_rp_initiated_logout(self, user):
        """Revoke the user's tokens.

        Copied and adapted from ``RPInitiatedLogoutView.do_logout()``."""

        # Delete Access Tokens if a user was found
        if oauth2_settings.OIDC_RP_INITIATED_LOGOUT_DELETE_TOKENS and not isinstance(
            user, AnonymousUser
        ):
            Application = get_application_model()  # pylint: disable=invalid-name

            access_tokens_to_delete = get_access_token_model().objects.filter(
                user=user,
                application__client_type__in=[
                    Application.CLIENT_PUBLIC,
                    Application.CLIENT_CONFIDENTIAL,
                ],
                application__authorization_grant_type__in=[
                    Application.GRANT_AUTHORIZATION_CODE,
                    Application.GRANT_IMPLICIT,
                    Application.GRANT_PASSWORD,
                    Application.GRANT_CLIENT_CREDENTIALS,
                    Application.GRANT_OPENID_HYBRID,
                ],
            )
            # This queryset has to be evaluated eagerly. The queryset would be empty with lazy
            # evaluation because `access_tokens_to_delete` represents an empty queryset once
            # `refresh_tokens_to_delete` is evaluated as all AccessTokens have been deleted.
            refresh_tokens_to_delete = list(
                get_refresh_token_model().objects.filter(
                    access_token__in=access_tokens_to_delete
                )
            )
            for token in access_tokens_to_delete:
                # Delete the token and its corresponding refresh and IDTokens.
                if token.id_token:
                    token.id_token.revoke()
                token.revoke()
            for refresh_token in refresh_tokens_to_delete:
                refresh_token.revoke()

    def get(self, request, *args, **kwargs):
        """Effectively log out the user if ``state`` match, otherwise prompt them"""

        state_key = request.GET.get("state")
        if not state_exists(request.session, state_key):
            return HttpResponseRedirect(settings.FRONTEND_LOGOUT_URL)

        # Retrieve the state before the session is flushed
        state = get_state(request.session, state_key)

        self.oauth2_provider_rp_initiated_logout(request.user)
        auth_logout(request)

        # Redirect to target page once the session has been cleared.
        return HttpResponseRedirect(
            state.get("post_logout_redirect_uri") or settings.LOGOUT_REDIRECT_URL
        )
