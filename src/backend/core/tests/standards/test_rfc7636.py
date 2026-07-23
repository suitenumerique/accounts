"""Unit tests for RFC 7636: Proof Key for Code Exchange by OAuth Public Clients."""

import pytest

from core.standards import rfc7636


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
