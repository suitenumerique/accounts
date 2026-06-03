from django.conf import settings
from django.shortcuts import resolve_url
from django.utils.encoding import force_str
from django.utils.functional import Promise

from social_django.strategy import DjangoStrategy


class OptionalSettingStrategy(DjangoStrategy):
    def get_setting(self, name):
        value = getattr(settings, name)
        if not value:  # Don't try to do stuff if the settings is falsy
            return value
        # Force text on URL named settings that are instance of Promise
        if name.endswith("_URL"):
            if isinstance(value, Promise):
                value = force_str(value)
            value = resolve_url(value)
        return value
