"""Accounts's custom strategies for Python Social Auth"""

from django.conf import settings

from social_django.strategy import DjangoStrategy


class OptionalURLSettingStrategy(DjangoStrategy):
    """Custom strategy to not resolve falsy settings suffixed by "_URL"."""

    def get_setting(self, name):
        value = getattr(settings, name)
        if not value:  # Don't try to do stuff if the settings is falsy
            return value
        return super().get_setting(name)
