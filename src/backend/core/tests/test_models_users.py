"""
Unit tests for the User model
"""

import contextlib

from django.core.exceptions import ValidationError

import pytest

from core import factories


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
