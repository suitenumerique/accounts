"""Utilities for analytics."""

import logging

from django.conf import settings

import posthog

logger = logging.getLogger(__name__)


def capture_event(
    event: str, *, distinct_id: str | None = None, properties: dict | None = None
) -> None:
    """Send a product event to PostHog, when PostHog is configured.

    Properties must stay free of user content (titles, file names, prompts).
    """
    if not settings.POSTHOG_KEY:
        return

    properties = properties if isinstance(properties, dict) else {}
    properties.setdefault("environment", settings.ENVIRONMENT)
    properties.setdefault("release", settings.RELEASE)
    posthog.capture(str(event), distinct_id=distinct_id, properties=properties)
