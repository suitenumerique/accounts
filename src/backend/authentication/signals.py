"""Signals for the authentication application."""

from core.utils import analytics


def django_auth_capture_event(*, event_name, user, **kwargs):
    """Signal receiver to capture events of django.contrib.auth"""
    analytics.capture_event(
        event_name,
        distinct_id=str(user.pk) if user else None,
    )
