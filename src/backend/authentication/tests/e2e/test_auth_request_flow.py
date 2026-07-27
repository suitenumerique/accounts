"""End-to-end tests for the complete ``AuthRequestBackend`` authentication flow."""

import random

from django.test import Client

from rest_framework import status

from core.factories import UserFactory
from core.standards import rfc7636

from authentication.models import AuthRequestStrategy


def test_full_auth_request_flow(client: Client):
    """An existing user should be authenticated at the end of the flow"""
    user = UserFactory()
    client_verifier, client_challenge = rfc7636.create_code_pair()

    # ---- Step 1: Create an authorization request for a user using its email
    response = client.post("/api/v1.0/auth/request/", data={"email": user.email})
    assert response.status_code == status.HTTP_200_OK, response.content
    auth_request_pk = response.json()["id"]

    # ---- Step 2: Create an authorization request attempt with the "password" strategy
    response = client.post(
        f"/api/v1.0/auth/request/{auth_request_pk}/attempt/",
        data={
            "strategy": AuthRequestStrategy.PASSWORD,
            "client_challenge": client_challenge,
        },
    )
    assert response.status_code == status.HTTP_200_OK, response.content
    auth_request_attempt_pk = response.json()["id"]

    # ---- Step 3: Try to log in using the previous authorization request attempt
    response = client.post(
        f"/api/v1.0/auth/request/{auth_request_pk}/attempt/{auth_request_attempt_pk}/login/",
        data={
            "secret": "password",  # Hardcoded in UserFactory()
            "client_verifier": client_verifier,
        },
    )
    assert response.status_code == status.HTTP_200_OK, response.content

    # ---- End: The user should now be logged in
    response = client.get("/api/v1.0/users/me/")
    assert response.status_code == status.HTTP_200_OK, response.content
    assert response.json()["id"] == str(user.pk)


def test_full_auth_request_flow_for_unknown_email(client: Client, faker):
    """A non-existing user's email should only be denied access at end of the flow"""
    client_verifier, client_challenge = rfc7636.create_code_pair()

    # ---- Step 1: Create an authorization request for a user using its email
    response = client.post("/api/v1.0/auth/request/", data={"email": faker.email()})
    assert response.status_code == status.HTTP_200_OK, response.content
    auth_request_pk = response.json()["id"]

    # ---- Step 2: Create an authorization request attempt with one of the permitted strategy
    response = client.post(
        f"/api/v1.0/auth/request/{auth_request_pk}/attempt/",
        data={
            # When the email is not known the strategy doesn't really matter as we are
            # bound to fail in the end, so better randomizing it to (eventually) catch
            # errors for this code path.
            "strategy": random.choice(list(AuthRequestStrategy)),
            "client_challenge": client_challenge,
        },
    )
    assert response.status_code == status.HTTP_200_OK, response.content
    auth_request_attempt_pk = response.json()["id"]

    # ---- Step 3: Try to log in using the previous authorization request attempt
    response = client.post(
        f"/api/v1.0/auth/request/{auth_request_pk}/attempt/{auth_request_attempt_pk}/login/",
        data={
            "secret": faker.pystr(),  # We still need to pass the serializer validation
            "client_verifier": client_verifier,
        },
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN, response.content

    # ---- End: The user shouldn't be logged in
    response = client.get("/api/v1.0/users/me/")
    assert response.status_code == status.HTTP_403_FORBIDDEN, response.content
