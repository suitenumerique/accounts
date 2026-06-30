"""Tests for Python Social Auth strategies."""

from django.urls import reverse

import pytest

from authentication.strategies import OptionalURLSettingStrategy


@pytest.mark.parametrize(
    "value,expected",
    [
        (None, None),
        ("", ""),
        ("http://foo.url", "http://foo.url"),
        ("authentication:login", reverse("authentication:login")),
    ],
    ids=repr,
)
def test_optional_url_setting_strategy(settings, value, expected):
    """Test OptionalURLSettingStrategy doesn't try to resolve the URL for falsy value."""
    settings.FOO_URL = value
    strategy = OptionalURLSettingStrategy(None)

    assert strategy.get_setting("FOO_URL") == expected
