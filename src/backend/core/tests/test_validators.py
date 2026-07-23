"""Unit tests for the accounts' core application's validators."""

import contextlib
import random
import re

from django.core.exceptions import ValidationError

import pytest

from core import validators
from core.standards import rfc3986


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


@pytest.mark.parametrize(
    "allowed_characters,value,expected_error",
    [
        pytest.param("", "", contextlib.nullcontext(), id="empty"),
        pytest.param(
            "",
            "a",
            pytest.raises(ValidationError, match="That character is not allowed: a."),
            id="character_not_allowed",
        ),
        pytest.param(
            "",
            "abc",
            pytest.raises(
                ValidationError, match="Those characters are not allowed: a,b,c."
            ),
            id="characters_not_allowed",
        ),
        pytest.param(
            "",
            "cba",
            pytest.raises(
                ValidationError, match="Those characters are not allowed: a,b,c."
            ),
            id="characters_not_allowed_are_sorted",
        ),
    ],
)
def test_characters_validator(allowed_characters, value, expected_error):
    """Test CharactersValidator()"""
    with expected_error:
        validators.CharactersValidator(allowed_characters)(value)


@pytest.mark.parametrize(
    "value,expected_error",
    [
        pytest.param("", contextlib.nullcontext(), id="empty"),
        pytest.param(
            rfc3986.UNRESERVED_CHARACTERS,
            contextlib.nullcontext(),
            id="unreserved",
        ),
        pytest.param(
            rfc3986.RESERVED_CHARACTERS,
            pytest.raises(
                ValidationError,
                match=re.escape(
                    "Only URI's unreserved characters are allowed. "
                    "Found: !,#,$,&,',(,),*,+,,,/,:,;,=,?,@,[,]."
                ),
            ),
            id="reserved",
        ),
    ],
)
def test_uri_unreserved_characters_validator(value, expected_error):
    """Test URIUnreservedCharactersValidator()"""
    with expected_error:
        validators.URIUnreservedCharactersValidator()(value)
