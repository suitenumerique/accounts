"""URL for the OIDC provider part of the project"""

from django.urls import include, path

from oauth2_provider import urls as oauth2_urls
from oauth2_provider import views as oauth2_views

from . import views

app_name = "oidc_provider"

urlpatterns = [
    # Replace oauth2_provider's confirmation template with the frontend page
    path(
        "logout/",
        views.RPInitiatedLogoutView.as_view(),
        name="rp-initiated-logout",
    ),
    # Override oauth2_provider's IntrospectTokenView
    path("introspect/", views.IntrospectTokenView.as_view(), name="introspect"),
    # Without OIDC_ISS_ENDPOINT, oauth2_provider derives the RFC 9207 `iss` authorization
    # response parameter from this route: it must live under the same prefix as the
    # OIDC discovery, otherwise `iss` falls back to the domain root.
    path(
        ".well-known/oauth-authorization-server",
        oauth2_views.OAuthServerMetadataView.as_view(),
        name="oauth-server-metadata",
    ),
    # Include the default oauth2_provider URLs for other endpoints but without the management views
    path("", include(oauth2_urls.base_urlpatterns + oauth2_urls.oidc_urlpatterns)),
]
