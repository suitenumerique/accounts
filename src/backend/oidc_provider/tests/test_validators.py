"""Tests for OIDC validators, especially the LaSuiteValidator."""

import base64
import json
from unittest.mock import MagicMock
from urllib.parse import parse_qs, urlparse

import pytest

from core.factories import UserFactory

from oidc_provider.factories import (
    CLIENT_SECRET,
    REDIRECT_URI,
    SimpleApplicationFactory,
)
from oidc_provider.validators import LaSuiteValidator

pytestmark = pytest.mark.django_db


def _make_request(user, scopes=None, claims=None):
    """Build a minimal mock OAuth2 request for unit tests."""
    request = MagicMock()
    request.user = user
    request.scopes = scopes or []
    request.claims = claims
    return request


def _decode_jwt_payload(token: str) -> dict:
    """Decode the payload of a JWT without verifying the signature."""
    payload_b64 = token.split(".")[1]
    # Add padding if needed
    padding = 4 - len(payload_b64) % 4
    if padding != 4:
        payload_b64 += "=" * padding
    return json.loads(base64.urlsafe_b64decode(payload_b64))


def _build_authorize_params(application, **overrides):
    """Return a default authorization request payload."""
    params = {
        "response_type": "code",
        "client_id": application.client_id,
        "redirect_uri": REDIRECT_URI,
        "scope": "openid email",
        "state": "test-state",
    }
    params.update(overrides)
    return params


def _get_authorization_code(client, application, user, **overrides):
    """Perform the authorization step and return the authorization code."""
    client.force_login(user)
    response = client.get(
        "/api/v1.0/o/authorize/",
        _build_authorize_params(application, **overrides),
    )
    assert response.status_code == 302

    params = parse_qs(urlparse(response["Location"]).query)
    assert "code" in params
    return params["code"][0]


def _exchange_code_for_tokens(client, application, code):
    """Exchange an authorization code for tokens and return the JSON payload."""
    response = client.post(
        "/api/v1.0/o/token/",
        {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": REDIRECT_URI,
            "client_id": application.client_id,
            "client_secret": CLIENT_SECRET,
        },
    )
    assert response.status_code == 200
    return response.json()


@pytest.fixture(name="use_lasuite_validator", autouse=True)
def fixture_use_lasuite_validator(settings):
    """Set the OAUTH2_VALIDATOR_CLASS to LaSuiteValidator for tests which need it."""
    settings.OAUTH2_PROVIDER = settings.OAUTH2_PROVIDER | {
        "OAUTH2_VALIDATOR_CLASS": "oidc_provider.validators.LaSuiteValidator",
    }


def test_acr_claim_included_when_claims_acr_equals_eidas1():
    """
    When request.claims contains {'acr': 'eidas1'}, the 'acr' claim
    must be present with value 'eidas1' in the returned additional claims.
    """
    user = UserFactory()
    request = _make_request(user, claims={"acr": "eidas1"})

    additional_claims = LaSuiteValidator().get_additional_claims(request)

    assert "acr" in additional_claims
    assert additional_claims["acr"] == "eidas1"


def test_acr_claim_absent_when_claims_is_none():
    """
    When request.claims is None, the 'acr' claim must NOT appear in the
    additional claims.
    """
    user = UserFactory()
    request = _make_request(user, claims=None)

    additional_claims = LaSuiteValidator().get_additional_claims(request)

    assert "acr" not in additional_claims


def test_acr_claim_absent_when_claims_is_empty_dict():
    """
    When request.claims is an empty dict, the 'acr' claim must NOT appear.
    """
    user = UserFactory()
    request = _make_request(user, claims={})

    additional_claims = LaSuiteValidator().get_additional_claims(request)

    assert "acr" not in additional_claims


def test_acr_claim_absent_when_acr_value_is_not_eidas1():
    """
    When request.claims contains 'acr' but with a value other than 'eidas1',
    the 'acr' claim must NOT appear in the additional claims.
    """
    user = UserFactory()
    request = _make_request(user, claims={"acr": "loa2"})

    additional_claims = LaSuiteValidator().get_additional_claims(request)

    assert "acr" not in additional_claims


def test_acr_claim_absent_when_claims_does_not_contain_acr_key():
    """
    When request.claims is a non-empty dict but does not contain the 'acr'
    key, the 'acr' claim must NOT appear in the additional claims.
    """
    user = UserFactory()
    request = _make_request(user, claims={"some_other": "value"})

    additional_claims = LaSuiteValidator().get_additional_claims(request)

    assert "acr" not in additional_claims


def test_id_token_contains_acr_eidas1_when_acr_values_requested(client):
    """
    When the authorization request includes 'acr_values=eidas1', the resulting
    id_token must carry the 'acr' claim with value 'eidas1'.

    This verifies the full chain:
    1. _create_authorization_code stores the acr claim on the grant.
    2. get_additional_claims reads it and adds it to the token.
    """
    application = SimpleApplicationFactory()
    user = UserFactory()

    code = _get_authorization_code(client, application, user, acr_values="eidas1")
    tokens = _exchange_code_for_tokens(client, application, code)

    id_token_payload = _decode_jwt_payload(tokens["id_token"])

    assert "acr" in id_token_payload, (
        "The 'acr' claim should be present in the id_token when acr_values=eidas1"
    )
    assert id_token_payload["acr"] == "eidas1"


def test_id_token_does_not_contain_acr_without_acr_values(client):
    """
    When the authorization request does NOT include 'acr_values', the resulting
    id_token must NOT contain the 'acr' claim.
    """
    application = SimpleApplicationFactory()
    user = UserFactory()

    code = _get_authorization_code(client, application, user)
    tokens = _exchange_code_for_tokens(client, application, code)

    id_token_payload = _decode_jwt_payload(tokens["id_token"])

    assert "acr" not in id_token_payload, (
        "The 'acr' claim should NOT be present in the id_token when acr_values is absent"
    )


def test_id_token_does_not_contain_acr_when_acr_values_not_eidas1(client):
    """
    When the authorization request includes 'acr_values' with a value other than
    'eidas1', the resulting id_token must NOT contain the 'acr' claim.
    """
    application = SimpleApplicationFactory()
    user = UserFactory()

    code = _get_authorization_code(client, application, user, acr_values="loa2")
    tokens = _exchange_code_for_tokens(client, application, code)

    id_token_payload = _decode_jwt_payload(tokens["id_token"])

    assert "acr" not in id_token_payload, (
        "The 'acr' claim should NOT be present when acr_values is not 'eidas1'"
    )
