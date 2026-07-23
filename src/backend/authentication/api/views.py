import secrets

from django.contrib import auth
from django.db import transaction

from rest_framework import status
from rest_framework.generics import get_object_or_404
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from authentication import models
from authentication.api import serializers


class AuthRequestView(APIView):
    def post(self, request: Request):
        serializer = serializers.AuthRequestSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        print(instance)
        print(instance.email, instance.user)


        return Response(serializer.data, status=status.HTTP_200_OK)


class AuthRequestAttemptView(APIView):
    @transaction.atomic()
    def post(self, request: Request, login_request_pk):
        login_request: models.AuthRequest = get_object_or_404(
            models.AuthRequest.objects.select_related("user"), pk=login_request_pk
        )
        if not login_request.is_active():
            return Response(status=status.HTTP_410_GONE)

        serializer = serializers.AuthRequestAttemptSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # TODO: Call the chosen Strategy
        match serializer.validated_data["strategy"]:
            case models.AuthRequestStrategy.PASSWORD:
                try:
                    # FIXME: Probably not need as we use `.check_password()` in `.fulfill()`
                    secret = login_request.user.password
                except AttributeError:
                    # A hash function shouldn't ever (hopefully) return an empty string so nothing
                    # will ever pass a `.compare_digest(hash(...), "")`, which is *theoretically*
                    # possible if we were to generate a random value, this will also expose us to
                    # timing attack since hashing take longer than accessing 2 Python attributes.
                    secret = ""
            case models.AuthRequestStrategy.DEVICE:
                secret = secrets.token_urlsafe()

        serializer.save(request=login_request, secret=secret)

        return Response(serializer.data, status=status.HTTP_200_OK)


class AuthRequestAttemptLoginView(APIView):
    @transaction.atomic()
    def post(self, request: Request, login_request_pk, login_request_attempt_pk):
        login_request_attempt: models.AuthRequestAttempt = get_object_or_404(
            models.AuthRequestAttempt.objects.select_related(
                "request__user"
            ).select_for_update(of=["self"], no_key=True),
            pk=login_request_attempt_pk,
            request__pk=login_request_pk,
        )
        if (
            not login_request_attempt.is_active()
            or not login_request_attempt.request.is_active()
        ):
            return Response(status=status.HTTP_410_GONE)

        serializer = serializers.AuthRequestAttemptLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        fulfilled = login_request_attempt.fulfill(
            serializer.validated_data["secret"],
            serializer.validated_data["client_verifier"],
        )
        if not fulfilled:
            return Response(status=status.HTTP_403_FORBIDDEN)

        # FIXME: Maybe a custom Django Authentication backend will fell less hacky and could be reusable?
        auth.login(request, login_request_attempt.request.user)
        return Response(status=status.HTTP_200_OK)
