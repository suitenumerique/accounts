"""API filters for Accounts' core application."""

import unicodedata

from django.conf import settings

import django_filters


def remove_accents(value):
    """Remove accents from a string (vélo -> velo)."""
    return "".join(
        c
        for c in unicodedata.normalize("NFD", value)
        if unicodedata.category(c) != "Mn"
    )


class UserSearchFilter(django_filters.FilterSet):
    """
    Custom filter for searching users.
    """

    q = django_filters.CharFilter(
        min_length=settings.API_USERS_SEARCH_QUERY_MIN_LENGTH, max_length=254
    )
