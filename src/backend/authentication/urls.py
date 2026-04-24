"""URL configuration for the authentication app."""

from django.urls import path

from . import views

urlpatterns = [
    path("login/", views.LoginRoutingView.as_view(), name="login"),
]
