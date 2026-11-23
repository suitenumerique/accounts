"""Import the users known by a product into accounts."""

import dataclasses
import itertools

from django.db import models, transaction
from django.utils.translation import gettext_lazy as _

from authentication.models import IdentityProviderName, IdentityProviderUser

from .models import User, UserSource

# The users are created by chunks, one transaction each, not to lock too many rows
# whatever the size of the batch sent by the product.
CREATE_CHUNK_SIZE = 500


class ImportStatus(models.TextChoices):
    """What accounts knows of an imported sub."""

    ACCOUNTS = "accounts", _("Already an accounts sub")
    IDENTITY_PROVIDER = "identity_provider", _("Identity provider sub of a user")
    CREATED = "created", _("User created")
    TO_CREATE = "to_create", _("User to create")
    EMAIL_CONFLICT = "email_conflict", _("Email of another user")
    AMBIGUOUS = "ambiguous", _("Sub of a user and identity provider sub of another")


@dataclasses.dataclass(frozen=True)
class ImportResult:
    """Status of an imported sub, with the accounts sub it matches, if any."""

    status: ImportStatus
    accounts_sub: str | None = None


def match_or_create_product_users(
    emails_by_sub: dict[str, str],
    *,
    provider: str = IdentityProviderName.PRO_CONNECT,
    dry_run: bool = False,
) -> dict[str, ImportResult]:
    """Match the subs of a product with accounts users, creating the unknown ones.

    A sub is matched with a user's sub, or with an identity provider's user id.
    The product does not tell which one it sent: a sub matching both, for two
    different users, is ambiguous and matched with neither. The email is never
    used to match a user: identity providers may
    return former emails. The unknown subs get a new user, with the sub as the
    identity provider's user id, unless their normalized email already belongs
    to another user. The users are created by chunks of CREATE_CHUNK_SIZE, one
    transaction each.

    The subs and emails must be validated by the caller: bulk_create skips the
    model validation.

    Matching a sub again returns the same accounts sub: imports can be replayed,
    e.g. after a chunk failed once the previous ones were created.
    """
    subs = list(emails_by_sub)

    # First, match the subs of the product with accounts users.
    # If the sub is found, the result is ImportStatus.ACCOUNTS,
    # and the accounts sub is the same as the product sub.
    results = {
        sub: ImportResult(ImportStatus.ACCOUNTS, sub)
        for sub in User.objects.filter(sub__in=subs).values_list("sub", flat=True)
    }
    # If the sub is found in the identity provider, the result is
    # ImportStatus.IDENTITY_PROVIDER, and the accounts sub is the sub of the
    # user this identity belongs to.
    # If the sub is found both as the sub of a user and as the identity of
    # another user, the result is ImportStatus.AMBIGUOUS, without an accounts
    # sub: picking one could associate the product user to the wrong person.
    for identity_sub, owner_sub in IdentityProviderUser.objects.filter(
        provider=provider, uid__in=subs
    ).values_list("uid", "user__sub"):
        if identity_sub not in results:
            results[identity_sub] = ImportResult(
                ImportStatus.IDENTITY_PROVIDER, owner_sub
            )
        # `identity_sub` is already the accounts sub of someone. It is ambiguous
        # when the identity belongs to another user.
        elif owner_sub != identity_sub:
            results[identity_sub] = ImportResult(ImportStatus.AMBIGUOUS)

    # The remaining subs are unknown. When their email already belongs to a
    # user, the result is ImportStatus.EMAIL_CONFLICT, without an accounts sub.
    # Otherwise the user is created: ImportStatus.TO_CREATE in a dry run, still
    # without an accounts sub, or ImportStatus.CREATED with the sub of the new
    # user.
    unknown = {
        sub: User.objects.normalize_email(email)
        for sub, email in emails_by_sub.items()
        if sub not in results
    }
    # Inactive users included: the email is unique.
    used_emails = set(
        User.objects.filter(email__in=unknown.values()).values_list("email", flat=True)
    )
    emails_to_create = {}
    for sub, email in unknown.items():
        if email in used_emails:
            results[sub] = ImportResult(ImportStatus.EMAIL_CONFLICT)
        else:
            used_emails.add(email)
            emails_to_create[sub] = email

    if dry_run:
        results.update(
            dict.fromkeys(emails_to_create, ImportResult(ImportStatus.TO_CREATE))
        )
        return results

    users_by_sub = {
        sub: User(email=email, source=UserSource.IMPORT)
        for sub, email in emails_to_create.items()
    }
    for user in users_by_sub.values():
        # bulk_create skips User.objects.create_user, which gives the users
        # created at login an unusable password: they log in with their
        # identity provider only.
        user.set_unusable_password()
    # Concurrent imports of the same people, by several products, must insert
    # the unique values in the same order: one waits for the other, then fails
    # on the unique constraint, instead of a deadlock.
    subs_by_email = sorted(users_by_sub, key=lambda sub: users_by_sub[sub].email)
    for chunk in itertools.batched(subs_by_email, CREATE_CHUNK_SIZE, strict=False):
        with transaction.atomic():
            User.objects.bulk_create(users_by_sub[sub] for sub in chunk)
            IdentityProviderUser.objects.bulk_create(
                IdentityProviderUser(user=users_by_sub[sub], provider=provider, uid=sub)
                for sub in sorted(chunk)
            )
    results.update(
        {
            sub: ImportResult(ImportStatus.CREATED, str(user.sub))
            for sub, user in users_by_sub.items()
        }
    )
    return results
