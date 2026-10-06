"""Authentication utilities functions."""

from authentication.models import IdentityProviderUser


def get_claim_from_identity_providers(
    identity_providers: list[IdentityProviderUser], claim_name: str
):
    """Retrieve claim values from associated identity providers"""
    return [
        s.extra_data[claim_name]
        for s in identity_providers
        if s.extra_data.get(claim_name) is not None
    ]
