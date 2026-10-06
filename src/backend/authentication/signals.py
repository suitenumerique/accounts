"""Signals for the authentication application."""

from core.utils import analytics


def django_auth_capture_event(*, event_name, user, **kwargs):
    """Signal receiver to capture events of django.contrib.auth"""
    analytics.capture_event(
        event_name,
        distinct_id=str(user.pk) if user else None,
    )


def django_user_logged_in_capture_event(*, user, **kwargs):
    """Signal receiver to capture events of django.contrib.auth.signals.user_logged_in"""
    # Import here to prevent apps not being loaded because of circular imports
    from authentication.utils import (  # noqa: PLC0415 pylint: disable=import-outside-toplevel
        get_claim_from_identity_providers,
    )

    person_properties = {
        "sub": user.sub,
        "email": user.email,
        "siret": get_claim_from_identity_providers(
            user.identity_providers.order_by("-updated_at"), "siret"
        ),
    }
    analytics.capture_event(
        "django:user_logged_in",
        distinct_id=str(user.pk),
        properties={
            **person_properties,
            "$set": person_properties,
        },
    )
