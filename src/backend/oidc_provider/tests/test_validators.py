"""Tests for OIDC validators, especially the LaSuiteValidator."""

import base64
import json
import time

import oauthlib.common
import pytest
from freezegun import freeze_time
from oauth2_provider.oauth2_validators import OAuth2Validator

from core.factories import UserFactory

from authentication.factories import IdentityProviderUserFactory
from authentication.models import IdentityProviderUser
from oidc_provider.factories import SimpleApplicationFactory
from oidc_provider.validators import LaSuiteValidator, OIDCValidator


def _make_request(user, scopes="", client=None):
    """Build a minimal OAuth2 request for unit tests."""
    return oauthlib.common.Request(
        "http://dummy-uri/",
        body={"user": user, "scopes": scopes, "client": client},
    )


def _decode_jwt_payload(token: str) -> dict:
    """Decode the payload of a JWT without verifying the signature."""
    payload_b64 = token.split(".")[1]
    # Add padding if needed
    padding = 4 - len(payload_b64) % 4
    if padding != 4:
        payload_b64 += "=" * padding
    return json.loads(base64.urlsafe_b64decode(payload_b64))


@pytest.fixture(name="validator", params=[OIDCValidator, LaSuiteValidator])
def validator_fixture(request) -> OAuth2Validator:
    """Pytest fixture that return an `OAuth2Validator` validator class."""
    return request.param()


def test_openid_scope(validator):
    """Test the `openid` scope claims: `sub`."""
    user = UserFactory()

    claims = validator.get_oidc_claims(None, None, _make_request(user, scopes="openid"))
    assert claims["sub"] == user.sub


def test_profile_scope(validator):
    """Test the `profile` scope claims: `given_name`, `name`."""
    user = UserFactory()

    claims = validator.get_oidc_claims(
        None, None, _make_request(user, scopes="profile")
    )
    assert claims["given_name"] == user.short_name
    assert claims["name"] == user.full_name


def test_email_scope(validator):
    """Test the `email` scope claims: `email`, `email_verified`."""
    user = UserFactory()

    claims = validator.get_oidc_claims(None, None, _make_request(user, scopes="email"))
    assert claims["email"] == user.email
    assert claims["email_verified"] is False


def test_email_scope_for_lasuite():
    """Test the `email` scope claims for LaSuiteValidator: `email`, `email_verified`."""
    user = UserFactory()
    request = _make_request(user, scopes="email")
    validator = LaSuiteValidator()

    claims = validator.get_oidc_claims(None, None, request)
    assert claims["email"] == user.email
    assert claims["email_verified"] is False

    # Link an identity, which hasn't verified the email
    IdentityProviderUserFactory(user=user, extra_data={"email_verified": False})
    claims = validator.get_oidc_claims(None, None, request)
    assert claims["email"] == user.email
    assert claims["email_verified"] is False

    # Link an additional identity, which has verified the email
    IdentityProviderUserFactory(user=user, extra_data={"email_verified": True})
    claims = validator.get_oidc_claims(None, None, request)
    assert claims["email"] == user.email
    assert claims["email_verified"] is True


def test_account_scope_for_lasuite():
    """Test the `account` scope claims for LaSuiteValidator: `guest`."""
    user = UserFactory()
    request = _make_request(user, scopes="account")
    validator = LaSuiteValidator()

    claims = validator.get_oidc_claims(None, None, request)
    assert claims["guest"] is False


def test_organization_scope_for_lasuite():
    """Test the `organization` scope claims for LaSuiteValidator: `siret`."""
    user = UserFactory()
    request = _make_request(user, scopes="organization")
    validator = LaSuiteValidator()

    claims = validator.get_oidc_claims(None, None, request)
    assert "siret" not in claims

    # Link an identity
    IdentityProviderUserFactory(user=user, extra_data={"siret": "1234567890123"})
    claims = validator.get_oidc_claims(None, None, request)
    assert claims["siret"] == "1234567890123"

    # Link an additional identity
    IdentityProviderUserFactory(user=user, extra_data={"siret": "3210987654321"})
    claims = validator.get_oidc_claims(None, None, request)
    assert claims["siret"] == "3210987654321"


def test_proconnect_scope_for_lasuite():
    """Test the `proconnect` scope claims for LaSuiteValidator: `proconnect:roles`."""
    user = UserFactory()
    request = _make_request(user, scopes="proconnect")
    validator = LaSuiteValidator()

    claims = validator.get_oidc_claims(None, None, request)
    assert "proconnect:roles" not in claims

    # Link an identity, which didn't provide roles
    IdentityProviderUserFactory(user=user, extra_data={"roles": None})
    claims = validator.get_oidc_claims(None, None, request)
    assert "proconnect:roles" not in claims

    # Link an additional identity, with roles
    IdentityProviderUserFactory(
        user=user, extra_data={"roles": ["agent_public", "agent_public_etat"]}
    )
    claims = validator.get_oidc_claims(None, None, request)
    assert claims["proconnect:roles"] == ["agent_public", "agent_public_etat"]

    # Link an additional identity, with no role
    IdentityProviderUserFactory(user=user, extra_data={"roles": []})
    claims = validator.get_oidc_claims(None, None, request)
    assert claims["proconnect:roles"] == []


def test_proconnect_scope_ignores_other_identity_providers_for_lasuite():
    """Test the `proconnect:roles` claim only comes from ProConnect identities."""
    user = UserFactory()
    request = _make_request(user, scopes="proconnect")
    validator = LaSuiteValidator()

    def create_other_identity_provider_user():
        """Create an identity of a provider other than ProConnect.

        ProConnect is the only supported provider yet, and `full_clean` rejects
        any other value: the `provider` is overridden directly in the database.
        To be replaced by a dedicated factory once another provider is supported.
        """
        identity_provider = IdentityProviderUserFactory(
            user=user, extra_data={"roles": ["admin"]}
        )
        IdentityProviderUser.objects.filter(pk=identity_provider.pk).update(
            provider="other-provider"
        )

    create_other_identity_provider_user()
    claims = validator.get_oidc_claims(None, None, request)
    assert "proconnect:roles" not in claims

    IdentityProviderUserFactory(user=user, extra_data={"roles": ["agent_public"]})
    create_other_identity_provider_user()
    claims = validator.get_oidc_claims(None, None, request)
    assert claims["proconnect:roles"] == ["agent_public"]


def test_proconnect_scope_not_requested_for_lasuite():
    """Test the `proconnect:roles` claim is not returned without the `proconnect` scope."""
    user = UserFactory()
    IdentityProviderUserFactory(user=user, extra_data={"roles": ["agent_public"]})

    claims = LaSuiteValidator().get_oidc_claims(
        None, None, _make_request(user, scopes="openid profile")
    )
    assert "proconnect:roles" not in claims


def test_get_userinfo_claims_with_proconnect_roles_for_lasuite(settings):
    """Test LaSuiteValidator's UserInfo JWT contains the `proconnect:roles` claim."""
    settings.OAUTH2_PROVIDER = {
        **settings.OAUTH2_PROVIDER,
        "OIDC_ISS_ENDPOINT": "http://issuer.domain",
    }
    user = UserFactory()
    client = SimpleApplicationFactory()
    IdentityProviderUserFactory(user=user, extra_data={"roles": ["agent_public"]})

    with freeze_time():
        userinfo = LaSuiteValidator().get_userinfo_claims(
            _make_request(user, scopes="openid proconnect", client=client)
        )
        now = int(time.time())

    assert _decode_jwt_payload(userinfo) == {
        "iat": now,
        "iss": "http://issuer.domain",
        "aud": client.client_id,
        "sub": user.sub,
        "proconnect:roles": ["agent_public"],
    }


@pytest.mark.parametrize("validator", [OIDCValidator], indirect=True)
def test_get_userinfo_claims(validator):
    """Test UserInfo is a dict containing the requested scopes' claims."""
    user = UserFactory()

    userinfo = validator.get_userinfo_claims(
        _make_request(user, scopes="openid profile")
    )
    assert userinfo == {
        "sub": user.sub,
        "given_name": user.short_name,
        "name": user.full_name,
    }


def test_get_userinfo_claims_for_lasuite(settings):
    """
    Test LaSuiteValidator's UserInfo is a JWT containing the requested scopes' claims
    and the `iss`, `aud` and `iat` claims.
    """
    settings.OAUTH2_PROVIDER = {
        **settings.OAUTH2_PROVIDER,
        "OIDC_ISS_ENDPOINT": "http://issuer.domain",
    }
    user = UserFactory()
    client = SimpleApplicationFactory()

    with freeze_time():
        userinfo = LaSuiteValidator().get_userinfo_claims(
            _make_request(user, scopes="openid profile", client=client)
        )
        now = int(time.time())

    assert _decode_jwt_payload(userinfo) == {
        "iat": now,
        "iss": "http://issuer.domain",
        "aud": client.client_id,
        "sub": user.sub,
        "given_name": user.short_name,
        "name": user.full_name,
    }
