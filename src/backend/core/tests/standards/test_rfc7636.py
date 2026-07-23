"""Unit tests for RFC 7636: Proof Key for Code Exchange by OAuth Public Clients."""

import pytest

from core.standards import rfc3986, rfc7636


@pytest.mark.parametrize("code_challenge_method", list(rfc7636.CodeChallengeMethod))
def test_create_code_pair(code_challenge_method):
    """Test create_code_pair() return verifiable code_verifier and code_challenge"""
    code_pair = rfc7636.create_code_pair(code_challenge_method)
    assert code_pair.verifier
    assert code_pair.challenge
    assert rfc7636.verify_code_verifier(
        *code_pair,
        code_challenge_method=code_challenge_method,
    )


def test_create_code_verifier():
    """Test create_code_verifier()"""

    # Test the default value
    assert len(rfc7636.create_code_verifier(length=None)) == 43

    # Test the lower bound
    with pytest.raises(
        ValueError, match="A code_verifier length must be between 43 and 128"
    ):
        rfc7636.create_code_verifier(length=42)

    # Test all possible length value
    for length in range(43, 128):
        code_verifier = rfc7636.create_code_verifier(length=length)
        assert len(code_verifier) == length
        assert set(code_verifier) <= set(rfc3986.UNRESERVED_CHARACTERS)

    # Test the upper bound
    with pytest.raises(
        ValueError, match="A code_verifier length must be between 43 and 128"
    ):
        rfc7636.create_code_verifier(length=129)


@pytest.mark.parametrize(
    "code_verifier,code_challenge_method,expected",
    [
        pytest.param(
            "dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk",
            "plain",
            "dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk",
            id="plain",
        ),
        pytest.param(
            "dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk",
            "S256",
            "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM",
            id="S256",
        ),
    ],
)
def test_create_code_challenge(code_verifier, code_challenge_method, expected):
    """Test create_code_challenge() for "plain" and "S256" code challenge method."""
    assert (
        rfc7636.create_code_challenge(code_verifier, code_challenge_method) == expected
    )


@pytest.mark.parametrize(
    "code_verifier,code_challenge,code_challenge_method",
    [
        pytest.param(
            "dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk",
            "dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk",
            "plain",
            id="plain",
        ),
        pytest.param(
            "dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk",
            "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM",
            "S256",
            id="S256",
        ),
    ],
)
def test_verify_code_verifier(code_verifier, code_challenge, code_challenge_method):
    """Test verify_code_verifier() for "plain" and "S256" code challenge method."""
    is_verified = rfc7636.verify_code_verifier(
        code_verifier,
        code_challenge,
        code_challenge_method,
    )
    assert is_verified is True
