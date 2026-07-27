"""URL configuration for the authentication app."""

from django.contrib.auth import views as auth_views
from django.urls import include, path

from . import views
from .api import views as api_views

app_name = "authentication"

urlpatterns = [
    path("login/", views.LoginRoutingView.as_view(), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path(
        "auth/request/",
        api_views.AuthRequestCreateView.as_view(),
        name="auth_request_create",
    ),
    path(
        "auth/request/<uuid:auth_request_pk>/attempt/",
        api_views.AuthRequestAttemptCreateView.as_view(),
        name="auth_request_attempt_create",
    ),
    path(
        "auth/request/<uuid:auth_request_pk>/attempt/<uuid:auth_request_attempt_pk>/",
        api_views.AuthRequestAttemptRetrieveView.as_view(),
        name="auth_request_attempt_retrieve",
    ),
    path(
        "auth/request/<uuid:auth_request_pk>/attempt/<uuid:auth_request_attempt_pk>/login/",
        api_views.AuthRequestAttemptLoginView.as_view(),
        name="auth_request_attempt_login",
    ),
    path(
        "oidc/",
        include("social_django.urls"),
    ),
]
