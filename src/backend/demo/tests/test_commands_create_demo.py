"""Test the `create_demo` management command"""

from unittest import mock

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import override_settings

import pytest

pytestmark = pytest.mark.django_db


@mock.patch(
    "demo.defaults.NB_OBJECTS",
    {
        "users": 10,
    },
)
@override_settings(DEBUG=True)
def test_commands_create_demo():
    """The create_demo management command should create objects as expected."""
    call_command("create_demo")

    assert get_user_model().objects.count() >= 10
