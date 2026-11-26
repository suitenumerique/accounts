"""Tests for the import of the users known by a product."""

from unittest import mock

from django.db import IntegrityError

import pytest

from core.factories import UserFactory

from authentication.factories import IdentityProviderUserFactory
from authentication.models import IdentityProviderUser
from users.imports import ImportResult, ImportStatus, match_or_create_product_users
from users.models import User, UserSource


@pytest.mark.parametrize(
    "email",
    [
        pytest.param("user@example.com", id="address"),
        pytest.param("user@whatever.tld", id="local_part"),
    ],
)
def test_match_or_create_product_users_accounts_sub(email):
    """A sub of an accounts user is returned as is, if its email is likewise."""
    user = UserFactory(email="user@example.com")

    assert match_or_create_product_users({user.sub: email}) == {
        user.sub: ImportResult(ImportStatus.ACCOUNTS, user.sub)
    }
    user.refresh_from_db()
    assert user.email == "user@example.com"
    assert User.objects.count() == 1
    assert not IdentityProviderUser.objects.exists()


@pytest.mark.parametrize(
    "email",
    [
        pytest.param("other@whatever.tld", id="address"),
        pytest.param("other@example.com", id="local_part"),
    ],
)
def test_match_or_create_product_users_ambiguous_accounts_sub(email):
    """A sub of an accounts user is ambiguous when the email is not likewise."""
    user = UserFactory(email="user@example.com")
    IdentityProviderUserFactory(uid=user.sub, user=user)

    assert match_or_create_product_users({user.sub: email}) == {
        user.sub: ImportResult(ImportStatus.AMBIGUOUS)
    }


def test_match_or_create_product_users_identity_provider_sub():
    """A sub of an identity provider's user returns the sub of its accounts user.

    Its email is not used.
    """
    identity = IdentityProviderUserFactory(
        uid="proconnect-sub", user__email="user@example.com"
    )

    assert match_or_create_product_users({"proconnect-sub": "other@example.com"}) == {
        "proconnect-sub": ImportResult(
            ImportStatus.IDENTITY_PROVIDER, identity.user.sub
        )
    }
    identity.user.refresh_from_db()
    assert identity.user.email == "user@example.com"
    assert User.objects.count() == 1
    assert IdentityProviderUser.objects.count() == 1


def test_match_or_create_product_users_ambiguous_identity_provider_sub():
    """A sub of a user, and identity provider sub of another, matches neither."""
    # first create a user with a sub
    user = UserFactory()
    # then create an identity provider user with the same sub value
    IdentityProviderUserFactory(uid=user.sub)

    # then try to import the user with a different email
    assert match_or_create_product_users({user.sub: "other@example.com"}) == {
        user.sub: ImportResult(ImportStatus.AMBIGUOUS)
    }
    assert User.objects.count() == 2


def test_match_or_create_product_users_accounts_sub_of_the_same_user():
    """A sub of a user, and identity provider sub of the same user, is not ambiguous."""
    user = UserFactory()
    IdentityProviderUserFactory(uid=user.sub, user=user)

    assert match_or_create_product_users({user.sub: user.email}) == {
        user.sub: ImportResult(ImportStatus.ACCOUNTS, user.sub)
    }


def test_match_or_create_product_users_creates_unknown_users():
    """An unknown sub creates an imported user identified by this sub."""
    results = match_or_create_product_users({"unknown-sub": " New@Example.com "})

    user = User.objects.get()
    assert results == {
        "unknown-sub": ImportResult(ImportStatus.CREATED, user.sub),
    }
    assert user.email == "new@example.com"
    assert user.source == UserSource.IMPORT
    assert not user.has_usable_password()
    identity = IdentityProviderUser.objects.get()
    assert identity.user == user
    assert identity.provider == "pro-connect"
    assert identity.uid == "unknown-sub"
    assert identity.extra_data == {}


def test_match_or_create_product_users_is_idempotent():
    """Importing a sub again returns the accounts sub of the created user."""
    result = match_or_create_product_users({"unknown-sub": "new@example.com"})
    assert result["unknown-sub"].status == ImportStatus.CREATED
    assert result["unknown-sub"].accounts_sub is not None

    created = match_or_create_product_users({"unknown-sub": "new@example.com"})[
        "unknown-sub"
    ]

    assert match_or_create_product_users({"unknown-sub": "new@example.com"}) == {
        "unknown-sub": ImportResult(
            ImportStatus.IDENTITY_PROVIDER, created.accounts_sub
        )
    }
    assert User.objects.count() == 1


def test_match_or_create_product_users_email_conflict():
    """An unknown sub whose email belongs to another user is not created.

    The import cannot resolve it on its own: the email is unique, so the user
    cannot be created, and an email is not enough to link the sub to the
    existing user, as identity providers may return former or reassigned
    emails. The conflict is reported to the product, which keeps its user
    unchanged. An inactive user and another case of the email conflict too.
    """
    UserFactory(email="taken@example.com", is_active=False)

    assert match_or_create_product_users({"unknown-sub": "Taken@example.com"}) == {
        "unknown-sub": ImportResult(ImportStatus.EMAIL_CONFLICT)
    }
    assert User.objects.count() == 1
    assert not IdentityProviderUser.objects.exists()


def test_match_or_create_product_users_email_conflict_in_the_same_batch():
    """Two unknown subs sharing an email: only the first one is created."""
    results = match_or_create_product_users(
        {"first-sub": "shared@example.com", "second-sub": "shared@example.com"}
    )

    assert results["first-sub"].status == ImportStatus.CREATED
    assert results["second-sub"] == ImportResult(ImportStatus.EMAIL_CONFLICT)
    assert User.objects.count() == 1
    assert IdentityProviderUser.objects.count() == 1
    assert IdentityProviderUser.objects.get().user == User.objects.get()
    assert IdentityProviderUser.objects.get().provider == "pro-connect"
    assert IdentityProviderUser.objects.get().uid == "first-sub"


def test_match_or_create_product_users_dry_run():
    """A dry run classifies the subs without creating anything."""
    user = UserFactory()
    identity = IdentityProviderUserFactory(uid="proconnect-sub")
    UserFactory(email="taken@example.com")

    results = match_or_create_product_users(
        {
            user.sub: user.email,
            "proconnect-sub": "whatever@example.com",
            "unknown-sub": "new@example.com",
            "conflict-sub": "taken@example.com",
        },
        dry_run=True,
    )

    assert results == {
        user.sub: ImportResult(ImportStatus.ACCOUNTS, user.sub),
        "proconnect-sub": ImportResult(
            ImportStatus.IDENTITY_PROVIDER, identity.user.sub
        ),
        "unknown-sub": ImportResult(ImportStatus.TO_CREATE),
        "conflict-sub": ImportResult(ImportStatus.EMAIL_CONFLICT),
    }
    assert User.objects.count() == 3
    assert IdentityProviderUser.objects.count() == 1


@mock.patch("users.imports.CREATE_CHUNK_SIZE", 2)
def test_match_or_create_product_users_by_chunks(django_assert_num_queries):
    """The users are created by chunks, one transaction each."""
    emails_by_sub = {f"sub-{i}": f"user-{i}@example.com" for i in range(5)}

    # Accounts subs, identity provider subs, used emails, then 3 chunks of a
    # transaction with the users and the identities creation.
    with django_assert_num_queries(3 + 3 * 4):
        results = match_or_create_product_users(emails_by_sub)

    assert {result.status for result in results.values()} == {ImportStatus.CREATED}
    assert User.objects.count() == 5
    assert set(IdentityProviderUser.objects.values_list("uid", flat=True)) == set(
        emails_by_sub
    )


def test_match_or_create_product_users_capture_events(
    settings, django_capture_on_commit_callbacks
):
    """A created user sends the events of a user created and associated at login."""
    settings.POSTHOG_KEY = {"id": "posthog-key", "host": "https://posthog.test"}

    with (
        mock.patch("posthog.capture") as posthog_capture_mock,
        django_capture_on_commit_callbacks(execute=True),
    ):
        match_or_create_product_users({"unknown-sub": "new@example.com"})

    user = User.objects.get()
    person_properties = {"sub": user.sub, "email": "new@example.com"}
    properties = {
        **person_properties,
        "$set": person_properties,
        "$set_once": {"source": "import"},
        "environment": settings.ENVIRONMENT,
        "release": settings.RELEASE,
    }
    assert posthog_capture_mock.call_args_list == [
        mock.call("account:created", distinct_id=str(user.pk), properties=properties),
        mock.call(
            "account:associated",
            distinct_id=str(user.pk),
            properties={
                "backend": "pro-connect",
                "backend_sub": "unknown-sub",
                **properties,
            },
        ),
    ]


def test_match_or_create_product_users_capture_no_events(
    settings, django_capture_on_commit_callbacks
):
    """The matched users, and the users of a dry run, send no events."""
    settings.POSTHOG_KEY = {"id": "posthog-key", "host": "https://posthog.test"}
    user = UserFactory()
    IdentityProviderUserFactory(uid="proconnect-sub")

    with (
        mock.patch("posthog.capture") as posthog_capture_mock,
        django_capture_on_commit_callbacks(execute=True),
    ):
        match_or_create_product_users(
            {user.sub: user.email, "proconnect-sub": "whatever@example.com"}
        )
        match_or_create_product_users({"unknown-sub": "new@example.com"}, dry_run=True)

    posthog_capture_mock.assert_not_called()


@mock.patch("users.imports.CREATE_CHUNK_SIZE", 2)
def test_match_or_create_product_users_failing_chunk(
    django_capture_on_commit_callbacks,
):
    """A failing chunk keeps the previous ones: the batch can be sent again."""
    emails_by_sub = {f"sub-{i}": f"user-{i}@example.com" for i in range(5)}
    bulk_create = IdentityProviderUser.objects.bulk_create
    calls = []

    def fail_on_second_chunk(*args, **kwargs):
        calls.append(None)
        if len(calls) == 2:
            raise IntegrityError
        return bulk_create(*args, **kwargs)

    with (
        mock.patch.object(
            IdentityProviderUser.objects,
            "bulk_create",
            side_effect=fail_on_second_chunk,
        ),
        pytest.raises(IntegrityError),
        django_capture_on_commit_callbacks() as callbacks,
    ):
        match_or_create_product_users(emails_by_sub)

    assert User.objects.count() == 2
    # Only the events of the first chunk are sent.
    assert len(callbacks) == 1

    results = match_or_create_product_users(emails_by_sub)

    assert sorted(result.status for result in results.values()) == [
        ImportStatus.CREATED,
        ImportStatus.CREATED,
        ImportStatus.CREATED,
        ImportStatus.IDENTITY_PROVIDER,
        ImportStatus.IDENTITY_PROVIDER,
    ]
    assert User.objects.count() == 5


def test_match_or_create_product_users_queries(django_assert_num_queries):
    """A chunk of users costs a constant number of queries, whatever its size."""
    emails_by_sub = {f"sub-{i}": f"user-{i}@example.com" for i in range(50)}

    # Accounts subs, identity provider subs, used emails, then the transaction
    # with the users and the identities creation.
    with django_assert_num_queries(7):
        match_or_create_product_users(emails_by_sub)

    assert User.objects.count() == 50
