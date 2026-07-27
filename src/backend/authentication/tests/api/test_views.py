"""Unit tests for the Authentication app's API views"""

from django.urls import reverse

from rest_framework import status

import core.factories

from authentication import factories


def test_auth_request_create_view_http_errors(client):
    """Test ``AuthRequestCreateView`` HTTP response status codes"""
    url = reverse("authentication:auth-request:create")

    client.force_login(core.factories.UserFactory())
    # 403 Forbidden
    response = client.post(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN, response.content


def test_auth_request_attempt_create_view_http_errors(faker, client):
    """Test ``AuthRequestAttemptCreateView`` HTTP response status codes"""
    auth_request_pk = faker.uuid4()
    url = reverse(
        "authentication:auth-request:attempt:create",
        kwargs={"auth_request_pk": auth_request_pk},
    )

    # 404 Not Found
    response = client.post(url)
    assert response.status_code == status.HTTP_404_NOT_FOUND, response.content

    # 410 Gone
    factories.AuthRequestFactory(pk=auth_request_pk, expired=True)
    response = client.post(url)
    assert response.status_code == status.HTTP_410_GONE, response.content

    # 403 Forbidden
    client.force_login(core.factories.UserFactory())
    response = client.post(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN, response.content


def test_auth_request_attempt_retrieve_view_http_errors(faker, client):
    """Test ``AuthRequestAttemptRetrieveView`` HTTP response status codes"""
    auth_request_pk, auth_request_attempt_pk = faker.uuid4(), faker.uuid4()
    url = reverse(
        "authentication:auth-request:attempt:retrieve",
        kwargs={
            "auth_request_pk": auth_request_pk,
            "auth_request_attempt_pk": auth_request_attempt_pk,
        },
    )

    # 403 Forbidden
    response = client.get(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN, response.content

    client.force_login(core.factories.UserFactory())
    # 404 Not Found
    response = client.get(url)
    assert response.status_code == status.HTTP_404_NOT_FOUND, response.content

    # 410 Gone
    factories.AuthRequestAttemptFactory(
        pk=auth_request_attempt_pk, request__pk=auth_request_pk, expired=True
    )
    response = client.get(url)
    assert response.status_code == status.HTTP_410_GONE, response.content


def test_auth_request_attempt_login_view_http_errors(faker, client):
    """Test ``AuthRequestAttemptLoginView`` HTTP response status codes"""
    auth_request_pk, auth_request_attempt_pk = faker.uuid4(), faker.uuid4()
    url = reverse(
        "authentication:auth-request:attempt:login",
        kwargs={
            "auth_request_pk": auth_request_pk,
            "auth_request_attempt_pk": auth_request_attempt_pk,
        },
    )

    # 404 Not Found
    response = client.post(url)
    assert response.status_code == status.HTTP_404_NOT_FOUND, response.content

    # 410 Gone
    factories.AuthRequestAttemptFactory(
        pk=auth_request_attempt_pk, request__pk=auth_request_pk, expired=True
    )
    response = client.post(url)
    assert response.status_code == status.HTTP_410_GONE, response.content

    client.force_login(core.factories.UserFactory())
    # 422 Unprocessable Content
    response = client.post(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN, response.content
