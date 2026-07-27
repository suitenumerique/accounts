"""Authentication app's API views"""

import secrets

from django.contrib import auth
from django.db import transaction

from rest_framework import status
from rest_framework.generics import get_object_or_404
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from core.api import permissions

from authentication import models
from authentication.api import serializers


class AuthRequestCreateView(APIView):
    """API view to create an ``AuthRequest``"""

    permission_classes = [permissions.IsNotAuthenticated]

    def post(self, request: Request):
        """
        - `200 OK` on success
        """

        serializer = serializers.AuthRequestSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_200_OK)


class AuthRequestAttemptCreateView(APIView):
    """API view to create an ``AuthRequestAttempt``"""

    permission_classes = [permissions.IsNotAuthenticated]

    def post(self, request: Request, auth_request_pk):
        """
        - `200 OK` on success
        - `404 NOT FOUND` when the ``AuthRequest`` doesn't exist
        - `410 GONE` when the ``AuthRequest`` can not be used anymore
        """

        login_request: models.AuthRequest = get_object_or_404(
            models.AuthRequest.objects.select_related("user"), pk=auth_request_pk
        )
        if not login_request.is_active():
            return Response(status=status.HTTP_410_GONE)

        serializer = serializers.AuthRequestAttemptCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # TODO: Maybe move that elsewhere?
        match serializer.validated_data["strategy"]:
            case models.AuthRequestStrategy.PASSWORD:
                # A hash function shouldn't ever (hopefully) return an empty string so nothing
                # will ever pass a `.compare_digest(hash(...), "")`, which is *theoretically*
                # possible if we were to generate a random value.
                secret = ""
            case models.AuthRequestStrategy.DEVICE:
                secret = secrets.token_urlsafe()

        serializer.save(request=login_request, secret=secret)

        return Response(serializer.data, status=status.HTTP_200_OK)


class AuthRequestAttemptRetrieveView(APIView):
    """API view to retrieve an ``AuthRequestAttempt``"""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request: Request, auth_request_pk, auth_request_attempt_pk):
        """
        - `200 OK` on success
        - `404 NOT FOUND` when the ``AuthRequest`` or ``AuthRequestAttempt`` doesn't exist
        - `410 GONE` when the ``AuthRequest`` or ``AuthRequestAttempt`` can not be used anymore
        """
        auth_request_attempt: models.AuthRequestAttempt = get_object_or_404(
            models.AuthRequestAttempt.objects.select_related("request__user"),
            pk=auth_request_attempt_pk,
            request__pk=auth_request_pk,
        )
        if (
            not auth_request_attempt.is_active()
            or not auth_request_attempt.request.is_active()
        ):
            return Response(status=status.HTTP_410_GONE)

        serializer = serializers.AuthRequestAttemptRetrieveSerializer(
            instance=auth_request_attempt
        )
        return Response(serializer.data, status=status.HTTP_200_OK)


class AuthRequestAttemptLoginView(APIView):
    """API view to log in user a previously created ``AuthRequestAttempt``"""

    permission_classes = [permissions.IsNotAuthenticated]

    @transaction.atomic()
    def post(self, request: Request, auth_request_pk, auth_request_attempt_pk):
        """
        - `200 OK` on success
        - `403 FORBIDDEN` when the authentification failed
        - `404 NOT FOUND` when the ``AuthRequest`` or ``AuthRequestAttempt`` doesn't exist
        - `410 GONE` when the ``AuthRequest`` or ``AuthRequestAttempt`` can not be used anymore
        """

        auth_request_attempt: models.AuthRequestAttempt = get_object_or_404(
            models.AuthRequestAttempt.objects.select_related(
                "request__user"
            ).select_for_update(of=["self"], no_key=True),
            pk=auth_request_attempt_pk,
            request__pk=auth_request_pk,
        )
        if (
            not auth_request_attempt.is_active()
            or not auth_request_attempt.request.is_active()
        ):
            return Response(status=status.HTTP_410_GONE)

        serializer = serializers.AuthRequestAttemptLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = auth.authenticate(
            request,
            auth_request_attempt=auth_request_attempt,
            secret=serializer.validated_data["secret"],
            client_verifier=serializer.validated_data["client_verifier"],
        )
        if not user:
            return Response(status=status.HTTP_403_FORBIDDEN)

        auth.login(request, user)
        return Response(status=status.HTTP_200_OK)
