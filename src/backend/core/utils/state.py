"""Utilities for OIDC-like state using the session."""

from django.conf import settings
from django.utils import crypto

SESSION_KEY = "_states"


def make_state_key(*, length=None) -> str:
    """Create a suitable value to be used as a state key."""
    return crypto.get_random_string(length=length or settings.SESSION_STATE_KEY_LENGTH)


def set_state(session, *, key: str | None = None, data=None):
    """Set, or update, the state in the session."""
    key = key or make_state_key()

    session.setdefault(SESSION_KEY, {})
    session[SESSION_KEY][key] = {
        "data": data or {}
    }  # namespace it to allow future metadata

    # Force immediate session save for cache-based backends
    session.modified = True
    session.save()

    return key


def get_state(session, key: str):
    """Retrieve the state's data"""
    return session[SESSION_KEY][key]["data"]


def state_exists(session, key: str) -> bool:
    """Check the state exists in the current session"""
    if not key:
        return False

    try:
        get_state(session, key)
    except KeyError:
        return False
    return True
