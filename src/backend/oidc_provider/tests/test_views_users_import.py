"""Tests for the users import endpoint."""

import base64
from unittest import mock

from django.db import IntegrityError

import pytest

from core.factories import UserFactory

from authentication.factories import IdentityProviderUserFactory
from oidc_provider.factories import (
    CLIENT_SECRET,
    ApplicationPolicyFactory,
    SimpleApplicationFactory,
)
from oidc_provider.views import UsersImportView
from users.imports import ImportStatus
from users.models import User, UserSource

URL = "/api/v1.0/o/users-import/"


def _build_basic_auth_headers(application, secret=CLIENT_SECRET):
    """Return HTTP Basic Auth headers for the OAuth2 client."""
    credentials = f"{application.client_id}:{secret}".encode()
    encoded_credentials = base64.b64encode(credentials).decode()
    return {"HTTP_AUTHORIZATION": f"Basic {encoded_credentials}"}


@pytest.fixture(name="application")
def application_fixture():
    """An application allowed to import users."""
    return ApplicationPolicyFactory(
        application=SimpleApplicationFactory(), import_users=True
    ).application


def _post(client, application, payload, **headers):
    return client.post(
        URL,
        payload,
        content_type="application/json",
        **(headers or _build_basic_auth_headers(application)),
    )


def test_users_import(client, application):
    """Each row is returned with its status and its accounts sub."""
    user = UserFactory()
    identity = IdentityProviderUserFactory(uid="proconnect-sub")
    UserFactory(email="taken@example.com")

    response = _post(
        client,
        application,
        {
            "users": [
                {"pk": 1, "sub": user.sub, "email": user.email},
                {"pk": 2, "sub": "proconnect-sub", "email": "old@example.com"},
                {"pk": 3, "sub": "unknown-sub", "email": "new@example.com"},
                {"pk": 4, "sub": "conflict-sub", "email": "taken@example.com"},
                {"pk": 5, "sub": "invalid-email-sub", "email": "not-an-email"},
                {"pk": 6, "email": "no-sub@example.com"},
                "not-a-row",
            ]
        },
    )

    assert response.status_code == 200
    created = User.objects.get(email="new@example.com")
    assert created.source == UserSource.IMPORT
    assert response.json() == {
        "counts": {
            ImportStatus.ACCOUNTS: 1,
            ImportStatus.IDENTITY_PROVIDER: 1,
            ImportStatus.CREATED: 1,
            ImportStatus.EMAIL_CONFLICT: 1,
            UsersImportView.INVALID_STATUS: 3,
        },
        "results": [
            {
                "pk": 1,
                "sub": user.sub,
                "status": ImportStatus.ACCOUNTS,
                "accounts_sub": user.sub,
            },
            {
                "pk": 2,
                "sub": "proconnect-sub",
                "status": ImportStatus.IDENTITY_PROVIDER,
                "accounts_sub": identity.user.sub,
            },
            {
                "pk": 3,
                "sub": "unknown-sub",
                "status": ImportStatus.CREATED,
                "accounts_sub": created.sub,
            },
            {
                "pk": 4,
                "sub": "conflict-sub",
                "status": ImportStatus.EMAIL_CONFLICT,
                "accounts_sub": None,
            },
            {
                "pk": 5,
                "sub": None,
                "status": UsersImportView.INVALID_STATUS,
                "accounts_sub": None,
            },
            {
                "pk": 6,
                "sub": None,
                "status": UsersImportView.INVALID_STATUS,
                "accounts_sub": None,
            },
            {
                "pk": None,
                "sub": None,
                "status": UsersImportView.INVALID_STATUS,
                "accounts_sub": None,
            },
        ],
    }


def test_users_import_same_sub_twice(client, application):
    """Rows sharing a sub, e.g. a sub and an email, get the same user."""
    response = _post(
        client,
        application,
        {
            "users": [
                {"pk": 1, "sub": "unknown-sub", "email": "first@example.com"},
                {"pk": 2, "sub": "unknown-sub", "email": "second@example.com"},
            ]
        },
    )

    assert response.status_code == 200
    user = User.objects.get()
    assert user.email == "first@example.com"
    assert [result["accounts_sub"] for result in response.json()["results"]] == [
        user.sub,
        user.sub,
    ]


def test_users_import_dry_run(client, application):
    """A dry run reports the users to create without creating them."""
    response = _post(
        client,
        application,
        {
            "users": [{"pk": 1, "sub": "unknown-sub", "email": "new@example.com"}],
            "dry_run": True,
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "counts": {ImportStatus.TO_CREATE: 1},
        "results": [
            {
                "pk": 1,
                "sub": "unknown-sub",
                "status": ImportStatus.TO_CREATE,
                "accounts_sub": None,
            }
        ],
    }
    assert not User.objects.exists()


@pytest.mark.usefixtures("application")
def test_users_import_unauthenticated(client):
    """The client must authenticate."""
    response = client.post(URL, {"users": []}, content_type="application/json")

    assert response.status_code == 401
    assert response.json()["error"] == "invalid_client"


def test_users_import_wrong_secret(client, application):
    """The client secret must be valid."""
    response = _post(
        client,
        application,
        {"users": []},
        **_build_basic_auth_headers(application, secret="wrong"),
    )

    assert response.status_code == 401


def test_users_import_bearer_token(client, application):
    """A Bearer token does not authenticate the client."""
    response = _post(
        client, application, {"users": []}, HTTP_AUTHORIZATION="Bearer some-token"
    )

    assert response.status_code == 401


@pytest.mark.parametrize("with_policy", [True, False])
def test_users_import_client_not_allowed(client, with_policy):
    """Only the clients whose policy allows it may import users."""
    application = SimpleApplicationFactory()
    if with_policy:
        ApplicationPolicyFactory(application=application, import_users=False)

    response = _post(
        client,
        application,
        {"users": [{"sub": "unknown-sub", "email": "new@example.com"}]},
    )

    assert response.status_code == 403
    assert response.json()["error"] == "unauthorized_client"
    assert not User.objects.exists()


@pytest.mark.parametrize(
    "payload", [[], {"users": "nope"}, {}], ids=["list", "users-str", "no-users"]
)
def test_users_import_invalid_payload(client, application, payload):
    """The body must hold a list of users."""
    response = _post(client, application, payload)

    assert response.status_code == 400
    assert response.json()["error"] == "invalid_request"


@pytest.mark.parametrize("dry_run", ["true", 1, None])
def test_users_import_invalid_dry_run(client, application, dry_run):
    """A dry run flag which is not a boolean is refused, nothing is created."""
    response = _post(
        client,
        application,
        {
            "users": [{"sub": "unknown-sub", "email": "new@example.com"}],
            "dry_run": dry_run,
        },
    )

    assert response.status_code == 400
    assert response.json()["error"] == "invalid_request"
    assert not User.objects.exists()


def test_users_import_not_json(client, application):
    """The body must be JSON."""
    response = client.post(
        URL,
        "users=nope",
        content_type="application/x-www-form-urlencoded",
        **_build_basic_auth_headers(application),
    )

    assert response.status_code == 400
    assert response.json()["error"] == "invalid_request"


def test_users_import_concurrent_import(client, application):
    """A conflict with a concurrent import asks the client to retry."""
    with mock.patch(
        "oidc_provider.views.match_or_create_product_users", side_effect=IntegrityError
    ):
        response = _post(
            client,
            application,
            {"users": [{"sub": "unknown-sub", "email": "new@example.com"}]},
        )

    assert response.status_code == 409
    assert response.json()["error"] == "conflict"


def test_users_import_get_not_allowed(client, application):
    """Only POST is allowed."""
    response = client.get(URL, **_build_basic_auth_headers(application))

    assert response.status_code == 405
