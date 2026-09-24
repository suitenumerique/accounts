"""Signals for the OIDC Provider application."""

from core.utils import analytics


def app_authorized_capture_event(*, request, token, **kwargs):
    """Signal receiver to capture events of oauth2_provider.signals.app_authorized"""
    analytics.capture_event(
        "oidc:token",
        distinct_id=str(token.user.pk) if token.user else None,
        properties={
            "grant_type": request.POST.get("grant_type"),
            "client_id": token.application.client_id,
            "application_name": token.application.name,
        },
    )
