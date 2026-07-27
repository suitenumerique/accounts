"""URL configuration for the authentication app."""

from django.contrib.auth import views as auth_views
from django.urls import include, path

from . import views
from .api import views as api_views

app_name = "authentication"


auth_request_attempt_urls = [
    path("", api_views.AuthRequestAttemptCreateView.as_view(), name="create"),
    path(
        "<uuid:auth_request_attempt_pk>/",
        api_views.AuthRequestAttemptRetrieveView.as_view(),
        name="retrieve",
    ),
    path(
        "<uuid:auth_request_attempt_pk>/login/",
        api_views.AuthRequestAttemptLoginView.as_view(),
        name="login",
    ),
]
auth_request_urls = [
    path("", api_views.AuthRequestCreateView.as_view(), name="create"),
    path(
        "<uuid:auth_request_pk>/attempt/",
        include((auth_request_attempt_urls, "attempt")),
    ),
]

urlpatterns = [
    path("login/", views.LoginRoutingView.as_view(), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path(
        "auth/request/",
        include((auth_request_urls, "auth-request")),
    ),
    path("oidc/", include("social_django.urls")),
]
