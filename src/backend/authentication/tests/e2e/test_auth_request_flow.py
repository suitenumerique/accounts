from django.test import Client

from rest_framework import status

from core.factories import UserFactory

from authentication.models import AuthRequestStrategy


def test_full_auth_request_flow(client: Client):
    user = UserFactory()

    # ---- Step 1: Create an authorization request for a user using its email
    response = client.post("/api/v1.0/auth/request/", data={"email": user.email})
    assert response.status_code == status.HTTP_200_OK, response.content
    auth_request_pk = response.json()["id"]

    # ---- Step 2: Create an authorization request attempt with one of the permitted strategy
    response = client.post(
        f"/api/v1.0/auth/request/{auth_request_pk}/attempt/",
        data={
            "strategy": AuthRequestStrategy.PASSWORD,
            # Example of https://www.rfc-editor.org/info/rfc7636/#appendix-B
            "client_challenge": "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM",
        },
    )
    assert response.status_code == status.HTTP_200_OK, response.content
    auth_request_attempt_pk = response.json()["id"]

    # ---- Step 3: Try to log in using the previous authorization request attempt
    response = client.post(
        f"/api/v1.0/auth/request/{auth_request_pk}/attempt/{auth_request_attempt_pk}/login/",
        data={
            "secret": "password",  # Hardcoded in UserFactory()
            # Example of https://www.rfc-editor.org/info/rfc7636/#appendix-B
            "client_verifier": "dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk",
        },
    )
    assert response.status_code == status.HTTP_200_OK, response.content

    # ---- End: The user should now be logged in
    response = client.get("/api/v1.0/users/me")
    assert response.json() == {"email": user.email}
