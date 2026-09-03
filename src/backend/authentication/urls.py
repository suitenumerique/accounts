"""URL configuration for the authentication app."""

from django.urls import include, path

from . import views

app_name = "authentication"

urlpatterns = [
    path("login/", views.LoginRoutingView.as_view(), name="login"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path("logout/end/", views.LogoutEndView.as_view(), name="logout-end"),
    path(
        "oidc/",
        include("social_django.urls"),
    ),
]
