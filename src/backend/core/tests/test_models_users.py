"""
Unit tests for the User model
"""

import contextlib

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

import pytest

from core import factories

User = get_user_model()


def test_models_users_str():
    """The str representation should be the email."""
    user = factories.UserFactory()
    assert str(user) == user.email


def test_models_users_id_unique():
    """The "id" field should be unique."""
    user = factories.UserFactory()
    with pytest.raises(ValidationError, match="User with this Id already exists."):
        factories.UserFactory(id=user.id)


@pytest.mark.parametrize(
    "sub,expected",
    [
        pytest.param(
            "325956d6-5de0-4c16-815e-54e9c4dbbc27", contextlib.nullcontext(), id="valid"
        ),
        pytest.param(
            "invalid süb",
            pytest.raises(
                ValidationError,
                match="Enter a valid sub. This value should be ASCII only.",
            ),
            id="ascii-only",
        ),
        pytest.param(
            12345,
            pytest.raises(ValidationError, match="Enter a valid UUID."),
            id="uuid-only",
        ),
    ],
)
def test_models_users_sub_validators(sub, expected):
    """The "sub" field should be validated."""
    with expected:
        factories.UserFactory(sub=sub)


def test_models_users_email_normalized_on_save():
    """The email of a user should be normalized when saved."""
    user = factories.UserFactory(email="John.Doe@Example.COM")
    user.refresh_from_db()
    assert user.email == "john.doe@example.com"

    user = factories.UserFactory(email="Dısk.Diſk@Example.com")
    user.refresh_from_db()
    assert user.email == "dısk.diſk@example.com"


def test_models_users_create_user_normalizes_email():
    """The manager should normalize the email of a created user."""
    user = User.objects.create_user(email=" Dısk@Example.COM ")
    user.refresh_from_db()
    assert user.email == "dısk@example.com"


def test_models_users_get_by_natural_key_email_matching():
    """Users should be found by email ignoring ASCII case only."""
    user = factories.UserFactory(email="disk@example.com")

    assert User.objects.get_by_natural_key("disk@example.com") == user
    assert User.objects.get_by_natural_key("DISK@EXAMPLE.COM") == user
    for email in ["dısk@example.com", "diſk@example.com", "disK@example.com"]:
        with pytest.raises(User.DoesNotExist):
            User.objects.get_by_natural_key(email)
