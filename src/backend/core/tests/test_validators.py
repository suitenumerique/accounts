"""Unit tests for the accounts' core application's validators."""

import contextlib
import random

from django.core.exceptions import ValidationError

import pytest

from core import validators


@pytest.mark.parametrize(
    "value,expected_error",
    [
        pytest.param("", contextlib.nullcontext(), id="empty"),
        pytest.param(
            "".join([chr(i) for i in range(127)]),
            contextlib.nullcontext(),
            id="all-ascii",
        ),
        pytest.param(
            chr(random.randint(0x80, 0x10FFFF)),
            pytest.raises(
                ValidationError,
                match="Enter a valid sub. This value should be ASCII only.",
            ),
            id="non-ascii-chr",
        ),
    ],
)
def test_sub_validator(value, expected_error):
    """Test validator raise an error on non-ascii character."""
    with expected_error:
        validators.sub_validator(value)
