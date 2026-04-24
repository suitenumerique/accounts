"""URL configuration for the core app."""

from django.conf import settings
from django.urls import include, path

from rest_framework.routers import DefaultRouter

from core.api import viewsets

# - Main endpoints
router = DefaultRouter()
router.register("users", viewsets.UserViewSet, basename="users")


urlpatterns = [
    path(
        f"api/{settings.API_VERSION}/",
        include(
            [
                *router.urls,
            ]
        ),
    ),
    path(f"api/{settings.API_VERSION}/config/", viewsets.ConfigView.as_view()),
]
