"""
Tests for the migration normalizing stored emails.
"""

import logging
from datetime import timedelta
from importlib import import_module

from django.apps import apps
from django.contrib.auth import get_user_model
from django.utils import timezone

import pytest

from core import factories

User = get_user_model()

migration = import_module("users.migrations.0006_normalize_emails")


def _user_with_stored_email(email):
    """Create a user storing the email as is, like the rows predating the normalization."""
    user = factories.UserFactory()
    User.objects.filter(pk=user.pk).update(email=email)
    return user


@pytest.mark.parametrize(
    "stored_email, expected_email",
    [
        ("John.Doe@Example.COM", "john.doe@example.com"),
        ("  john.doe@example.com ", "john.doe@example.com"),
        ("john.doe@example.com", "john.doe@example.com"),
        ("Dısk@Example.com", "dısk@example.com"),
        ("Diſk@Example.com", "diſk@example.com"),
        ("DisK@Example.com", "disK@example.com"),
    ],
)
def test_migrations_normalize_emails(stored_email, expected_email):
    """Only the surrounding spaces and the ASCII case of emails should change."""
    user = _user_with_stored_email(stored_email)

    migration.forward(apps, None)

    user.refresh_from_db()
    assert user.email == expected_email


def test_migrations_normalize_emails_duplicate_kept(caplog):
    """A user whose normalized email is already taken should keep its email."""
    upper_user = _user_with_stored_email("Marie.Dupont@example.com")
    lower_user = _user_with_stored_email("marie.dupont@example.com")
    other_user = _user_with_stored_email("John.Doe@example.com")

    with caplog.at_level(logging.ERROR):
        migration.forward(apps, None)

    upper_user.refresh_from_db()
    lower_user.refresh_from_db()
    other_user.refresh_from_db()
    assert upper_user.email == "Marie.Dupont@example.com"
    assert lower_user.email == "marie.dupont@example.com"
    assert other_user.email == "john.doe@example.com"
    assert (
        f"Email of user {upper_user.pk} not normalized, already used by user "
        f"{lower_user.pk}"
    ) in caplog.text
    assert "dupont" not in caplog.text.lower()


def test_migrations_normalize_emails_duplicate_last_logged_in(caplog):
    """When several users normalize to the same email, the last logged in gets it."""
    # create an older user and make sure it's not the last logged in
    older_user = _user_with_stored_email("Marie.Dupont@example.com")
    User.objects.filter(pk=older_user.pk).update(
        created_at=timezone.now() - timedelta(days=2),
        last_login=timezone.now() - timedelta(days=30),
    )

    # create a newer user and make sure it's the last logged in
    logged_in_user = _user_with_stored_email("MARIE.DUPONT@example.com")
    User.objects.filter(pk=logged_in_user.pk).update(last_login=timezone.now())

    # create a never logged in user
    never_logged_in_user = _user_with_stored_email("marie.Dupont@example.com")

    # run the migration
    with caplog.at_level(logging.ERROR):
        migration.forward(apps, None)

    # check the results
    older_user.refresh_from_db()
    logged_in_user.refresh_from_db()
    never_logged_in_user.refresh_from_db()

    # the last logged in user gets the normalized email
    assert logged_in_user.email == "marie.dupont@example.com"
    # the older user keeps its email
    assert older_user.email == "Marie.Dupont@example.com"
    # the never logged in user keeps its email
    assert never_logged_in_user.email == "marie.Dupont@example.com"
    # an error is logged for each of them
    for user in [older_user, never_logged_in_user]:
        assert (
            f"Email of user {user.pk} not normalized, already used by user "
            f"{logged_in_user.pk}"
        ) in caplog.text


def test_migrations_normalize_emails_duplicate_never_logged_in(caplog):
    """When none of the users ever logged in, the oldest one gets the email."""
    older_user = _user_with_stored_email("Marie.Dupont@example.com")
    newer_user = _user_with_stored_email("MARIE.DUPONT@example.com")

    with caplog.at_level(logging.ERROR):
        migration.forward(apps, None)

    newer_user.refresh_from_db()
    older_user.refresh_from_db()
    assert older_user.email == "marie.dupont@example.com"
    assert newer_user.email == "MARIE.DUPONT@example.com"
    assert (
        f"Email of user {newer_user.pk} not normalized, already used by user "
        f"{older_user.pk}"
    ) in caplog.text


def test_migrations_normalize_emails_queries(django_assert_num_queries):
    """The emails should be updated in batches, not one query per user."""
    for index in range(3):
        _user_with_stored_email(f"User{index}@Example.com")

    # One query to read the emails, one to update them in a single batch
    with django_assert_num_queries(2):
        migration.forward(apps, None)
