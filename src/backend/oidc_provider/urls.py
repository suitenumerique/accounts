"""URL for the OIDC provider part of the project"""

from django.urls import include, path

from oauth2_provider import urls as oauth2_urls

from . import views

urlpatterns = [
    # Override path("introspect/", views.IntrospectTokenView.as_view(), name="introspect"),
    path("introspect/", views.IntrospectTokenView.as_view(), name="introspect"),
    # Include the default oauth2_provider URLs for other endpoints like authorize, token, etc.
    path("", include(oauth2_urls)),
]
