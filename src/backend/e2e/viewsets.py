"""Viewsets for the e2e app."""

from django.contrib.auth import get_user_model, login

import rest_framework as drf
from rest_framework import response as drf_response
from rest_framework import status
from rest_framework.permissions import AllowAny

from e2e.serializers import E2EAuthSerializer


class UserAuthViewSet(drf.viewsets.ViewSet):
    """Viewset to handle user authentication for E2E tests."""

    permission_classes = [AllowAny]
    authentication_classes = []

    def create(self, request):
        """
        POST /api/v1.0/e2e/user-auth/

        Create a user with the given email if it doesn't exist and log them in.
        This bypasses the OIDC/Keycloak flow and is only available when
        ``LOAD_E2E_URLS`` is enabled (never in production).
        """
        serializer = E2EAuthSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = (
            get_user_model()
            .objects.filter(email=serializer.validated_data["email"])
            .first()
        )
        if not user:
            user = get_user_model()(email=serializer.validated_data["email"])
            user.set_unusable_password()
            user.save()

        login(request, user, "django.contrib.auth.backends.ModelBackend")

        return drf_response.Response({"email": user.email}, status=status.HTTP_200_OK)
