"""Accounts's custom classes for Python Social Auth."""

from django.conf import settings

from social_django.models import DjangoStorage
from social_django.strategy import DjangoStrategy

from authentication.models import IdentityProviderUser


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
