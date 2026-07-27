"""Unit tests for the Authentication app's API serializers"""  # pylint: disable=C0116

import random

from django.utils.crypto import get_random_string

import pytest

import core.factories
from core.standards import rfc3986, rfc7636
from core.testing.rest_framework import assert_errors_code
from core.utils.datetime import normalize_zero_utc_offset

from authentication import factories, models
from authentication.api import serializers


def test_auth_request_serializer_serialization():
    auth_request = factories.AuthRequestFactory()

    serializer = serializers.AuthRequestSerializer(instance=auth_request)
    assert serializer.data == {
        "id": str(auth_request.pk),
        "expires_at": normalize_zero_utc_offset(auth_request.expires_at),
    }


def test_auth_request_serializer_deserialization(faker):
    data = {"email": faker.email()}

    serializer = serializers.AuthRequestSerializer(data=data)
    assert serializer.is_valid(), serializer.errors
    assert serializer.validated_data == data


@pytest.mark.parametrize(
    "data,expected",
    [
        pytest.param(
            {},
            {"email": ["required"]},
            id="fields_required",
        ),
        pytest.param(
            {"email": None},
            {"email": ["null"]},
            id="fields_null",
        ),
        pytest.param({"email": ""}, {"email": ["blank"]}, id="fields_blank"),
    ],
)
def test_auth_request_serializer_deserialization_errors(data, expected):
    serializer = serializers.AuthRequestSerializer(data=data)
    assert not serializer.is_valid()
    assert_errors_code(serializer.errors, expected)


def test_auth_request_serializer_save_when_the_email_is_known():
    user = core.factories.UserFactory()

    serializer = serializers.AuthRequestSerializer(data={"email": user.email})
    serializer.is_valid(raise_exception=True)
    auth_request = serializer.save()
    assert auth_request.user == user
    assert auth_request.email == ""


def test_auth_request_serializer_save_when_the_email_is_not_known(faker):
    data = {"email": faker.email()}

    serializer = serializers.AuthRequestSerializer(data=data)
    serializer.is_valid(raise_exception=True)
    auth_request = serializer.save()
    assert auth_request.user is None
    assert auth_request.email == data["email"]


def test_auth_request_attempt_create_serializer_serialization():
    auth_request_attempt = factories.AuthRequestAttemptFactory(
        client_challenge=rfc7636.create_code_pair().challenge,
    )

    serializer = serializers.AuthRequestAttemptCreateSerializer(
        instance=auth_request_attempt
    )
    assert serializer.data == {
        "id": str(auth_request_attempt.pk),
        "strategy": auth_request_attempt.strategy,
        "client_challenge": auth_request_attempt.client_challenge,
        "expires_at": normalize_zero_utc_offset(auth_request_attempt.expires_at),
    }


def test_auth_request_attempt_create_serializer_deserialization():
    data = {
        "strategy": random.choice(list(models.AuthRequestStrategy)),
        "client_challenge": rfc7636.create_code_pair().challenge,
    }

    serializer = serializers.AuthRequestAttemptCreateSerializer(data=data)
    assert serializer.is_valid(), serializer.errors
    assert serializer.validated_data == data


@pytest.mark.parametrize(
    "data,expected",
    [
        pytest.param(
            {},
            {"strategy": ["required"], "client_challenge": ["required"]},
            id="fields_required",
        ),
        pytest.param(
            {"strategy": None, "client_challenge": None},
            {"strategy": ["null"], "client_challenge": ["null"]},
            id="fields_null",
        ),
        pytest.param(
            {"strategy": "", "client_challenge": ""},
            {"strategy": ["invalid_choice"], "client_challenge": ["blank"]},
            id="fields_blank",
        ),
        pytest.param(
            {
                "strategy": random.choice(list(models.AuthRequestStrategy)),
                "client_challenge": get_random_string(
                    42, rfc3986.UNRESERVED_CHARACTERS
                ),
            },
            {"client_challenge": ["min_length"]},
            id="client_challenge_min_length",
        ),
        pytest.param(
            {
                "strategy": random.choice(list(models.AuthRequestStrategy)),
                "client_challenge": get_random_string(
                    129, rfc3986.UNRESERVED_CHARACTERS
                ),
            },
            {"client_challenge": ["max_length"]},
            id="client_challenge_max_length",
        ),
        pytest.param(
            {
                "strategy": random.choice(list(models.AuthRequestStrategy)),
                "client_challenge": (
                    get_random_string(42, rfc3986.UNRESERVED_CHARACTERS)
                    + random.choice(rfc3986.RESERVED_CHARACTERS)
                ),
            },
            {"client_challenge": ["only_uri_unreserved_characters"]},
            id="client_challenge_only_uri_unreserved_characters",
        ),
    ],
)
def test_auth_request_attempt_create_serializer_deserialization_errors(data, expected):
    serializer = serializers.AuthRequestAttemptCreateSerializer(data=data)
    assert not serializer.is_valid()
    assert_errors_code(serializer.errors, expected)


def test_auth_request_attempt_retrieve_serializer_serialization():
    auth_request_attempt = factories.AuthRequestAttemptFactory(fulfilled=True)

    serializer = serializers.AuthRequestAttemptRetrieveSerializer(
        instance=auth_request_attempt
    )
    assert serializer.data == {
        "id": str(auth_request_attempt.pk),
        "strategy": auth_request_attempt.strategy,
        "secret": "",
        "fulfilled_at": normalize_zero_utc_offset(auth_request_attempt.fulfilled_at),
        "expires_at": normalize_zero_utc_offset(auth_request_attempt.expires_at),
        "created_at": normalize_zero_utc_offset(auth_request_attempt.created_at),
    }


def test_auth_request_attempt_login_serializer_deserialization(faker):
    data = {
        "client_verifier": rfc7636.create_code_verifier(),
        "secret": faker.sentence(),
    }

    serializer = serializers.AuthRequestAttemptLoginSerializer(data=data)
    assert serializer.is_valid(), serializer.errors
    assert serializer.validated_data == data


@pytest.mark.parametrize(
    "data,expected",
    [
        pytest.param(
            {},
            {"secret": ["required"], "client_verifier": ["required"]},
            id="fields_required",
        ),
        pytest.param(
            {"secret": None, "client_verifier": None},
            {"secret": ["null"], "client_verifier": ["null"]},
            id="fields_null",
        ),
        pytest.param(
            {"secret": "", "client_verifier": ""},
            {"secret": ["blank"], "client_verifier": ["blank"]},
            id="fields_blank",
        ),
        pytest.param(
            {
                "secret": "S3cr3tS",
                "client_verifier": get_random_string(42, rfc3986.UNRESERVED_CHARACTERS),
            },
            {"client_verifier": ["min_length"]},
            id="client_verifier_min_length",
        ),
        pytest.param(
            {
                "secret": "S3cr3tS",
                "client_verifier": get_random_string(
                    129, rfc3986.UNRESERVED_CHARACTERS
                ),
            },
            {"client_verifier": ["max_length"]},
            id="client_verifier_max_length",
        ),
        pytest.param(
            {
                "secret": "S3cr3tS",
                "client_verifier": (
                    get_random_string(42, rfc3986.UNRESERVED_CHARACTERS)
                    + random.choice(rfc3986.RESERVED_CHARACTERS)
                ),
            },
            {"client_verifier": ["only_uri_unreserved_characters"]},
            id="client_verifier_only_uri_unreserved_characters",
        ),
    ],
)
def test_auth_request_attempt_login_serializer_deserialization_errors(data, expected):
    serializer = serializers.AuthRequestAttemptLoginSerializer(data=data)
    assert not serializer.is_valid()
    assert_errors_code(serializer.errors, expected)
