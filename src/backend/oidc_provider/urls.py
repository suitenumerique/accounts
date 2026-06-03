"""URL for the OIDC provider part of the project"""

from django.urls import include, path

from oauth2_provider import urls as oauth2_urls

from . import views

urlpatterns = [
    # Override oauth2_provider's IntrospectTokenView
    path("introspect/", views.IntrospectTokenView.as_view(), name="introspect"),
    # Include the default oauth2_provider URLs for other endpoints but without the management views
    path("", include(oauth2_urls.base_urlpatterns + oauth2_urls.oidc_urlpatterns)),
]
