"""Unit tests for RFC 3986: Uniform Resource Identifier (URI): Generic Syntax."""

import collections
import string

from core.standards import rfc3986


def test_reserved_and_unreserved_characters_alphabet():
    """Test that our reserved and unreserved characters are the complete URI allowed alphabet"""
    assert set(rfc3986.RESERVED_CHARACTERS + rfc3986.UNRESERVED_CHARACTERS) == set(
        string.ascii_letters + string.digits + ":/?#[]@!$&'()*+,;=-._~"
    )


def test_reserved_and_unreserved_characters_occurrence():
    """Test that our reserved and unreserved characters doesn't have duplicate"""
    alphabet = rfc3986.RESERVED_CHARACTERS + rfc3986.UNRESERVED_CHARACTERS
    assert collections.Counter(alphabet).total() == len(set(alphabet))


def test_reserved_and_unreserved_characters_do_not_overlap():
    """Test that our reserved and unreserved characters lists are disjoint"""
    assert (
        set(rfc3986.RESERVED_CHARACTERS) & set(rfc3986.UNRESERVED_CHARACTERS) == set()
    )
