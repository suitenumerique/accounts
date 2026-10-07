"""Accounts's custom classes for Python Social Auth."""

from django.conf import settings

from social_django.models import DjangoStorage
from social_django.strategy import DjangoStrategy

from core.utils import analytics

from authentication.models import IdentityProviderUser
from authentication.utils import get_claim_from_identity_providers


class OptionalURLSettingStrategy(DjangoStrategy):
    """Custom strategy to not resolve falsy settings suffixed by "_URL"."""

    def get_setting(self, name):
        value = getattr(settings, name)
        if not value:  # Don't try to do stuff if the settings is falsy
            return value
        return super().get_setting(name)


class AccountsDjangoStorage(DjangoStorage):
    """Custom storage to encrypt the `extra_data` content."""

    user = IdentityProviderUser


def capture_events(
    *args,
    **kwargs,
):
    """Pipeline function to capture analytics events."""
    user, is_new, new_association = (
        kwargs["user"],
        kwargs["is_new"],
        kwargs["new_association"],
    )
    if not any([is_new, new_association]):
        return None

    person_properties = {
        "sub": user.sub,
        "email": user.email,
        "siret": get_claim_from_identity_providers(
            user.identity_providers.order_by("-updated_at"), "siret"
        ),
    }
    if is_new:
        analytics.capture_event(
            "account:created",
            distinct_id=str(user.pk),
            properties={
                **person_properties,
                "$set": person_properties,
            },
        )
    if new_association:
        analytics.capture_event(
            "account:associated",
            distinct_id=str(user.pk),
            properties={
                "backend": kwargs["social"].provider,
                "backend_sub": kwargs["social"].uid,
                **person_properties,
                "$set": person_properties,
            },
        )
    return None
