"""URL configuration for the authentication app."""

from django.contrib.auth import views as auth_views
from django.urls import include, path

from . import views

app_name = "authentication"

urlpatterns = [
    path("login/", views.LoginRoutingView.as_view(), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path(
        "oidc/",
        include("social_django.urls"),
    ),
]
