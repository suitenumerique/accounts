"""
Module for OIDC authentication.

Contains all related code for OIDC authentication flow between
Accounts and the products.
"""

import json

from jwcrypto import jwt
from oauth2_provider.models import AbstractApplication
from oauth2_provider.oauth2_validators import OAuth2Validator

from authentication.models import IdentityProviderUser


class OIDCValidator(OAuth2Validator):
    """
    Base Validator of the project, it only supports officials
    OIDC scopes and claims that are available in Accounts.
    """

    oidc_claim_scope = {
        "sub": "openid",
        # Claims for "email" scope
        "email": "email",
        "email_verified": "email",
        # Claims for "profile" scope
        "given_name": "profile",
        "name": "profile",
    }

    def get_discovery_claims(self, request):
        return super().get_discovery_claims(request) + list(
            self.oidc_claim_scope.keys()
        )

    def get_additional_claims(self, request):
        """
        Generate additional claims to be included in the token.

        Args:
            request: The OAuth2 request object containing user and scope information.

        Returns:
            dict: A dictionary of additional claims to be included in the token.
        """
        additional_claims = super().get_additional_claims(request)

        additional_claims["sub"] = str(request.user.sub)

        # "email" claims
        additional_claims["email"] = request.user.email
        additional_claims["email_verified"] = False

        # "profile" claims
        additional_claims["given_name"] = request.user.short_name
        additional_claims["name"] = request.user.full_name

        return additional_claims

    def validate_silent_authorization(self, request):
        """Ensure the logged in user has authorized silent OpenID authorization.

        Silent OpenID authorization allows access tokens and id tokens to be
        granted to clients without any user prompt or interaction.

        :param request: OAuthlib request.
        :type request: oauthlib.common.Request
        :rtype: True or False

        Method is used by:
            - OpenIDConnectAuthCode
            - OpenIDConnectImplicit
            - OpenIDConnectHybrid
        """
        return request.user.is_authenticated

    def validate_silent_login(self, request):
        """Ensure session user has authorized silent OpenID login.

        If no user is logged in or has not authorized silent login, this
        method should return False.

        If the user is logged in but associated with multiple accounts and
        not selected which one to link to the token then this method should
        raise an oauthlib.oauth2.AccountSelectionRequired error.

        :param request: OAuthlib request.
        :type request: oauthlib.common.Request
        :rtype: True or False

        Method is used by:
            - OpenIDConnectAuthCode
            - OpenIDConnectImplicit
            - OpenIDConnectHybrid
        """
        return request.user.is_authenticated

    def introspect_token(self, *args, **kwargs):
        # `django-oauth-toolkit` doesn't use the validator in its
        # `IntrospectTokenView` (which we copied) so the method is no use to
        # us and shouldn't be called, but pylint want it implemented.
        raise Exception("Not Implemented")  # pylint: disable=broad-exception-raised


class LaSuiteValidator(OIDCValidator):
    """
    Validator to be used for the LaSuite projects, it adds additional
    claims to support migration from ProConnect to Accounts.
    """

    oidc_claim_scope = OIDCValidator.oidc_claim_scope | {
        # Claims for "organization" scope
        "siret": "organization",
    }

    def _get_claim_from_identity_providers(
        self, identity_providers: list[IdentityProviderUser], claim
    ):
        return [
            s.extra_data[claim]
            for s in identity_providers
            if s.extra_data.get(claim) is not None
        ]

    def get_additional_claims(self, request):
        """
        Generate additional claims to be included in the token.

        Args:
            request: The OAuth2 request object containing user and scope information.

        Returns:
            dict: A dictionary of additional claims to be included in the token.
        """
        additional_claims = super().get_additional_claims(request)
        identity_providers = list(
            request.user.identity_providers.order_by("-updated_at")
        )

        # "email" claims
        additional_claims["email_verified"] |= any(
            self._get_claim_from_identity_providers(
                identity_providers, "email_verified"
            )
        )

        # "organization" claims
        identity_providers_siret = self._get_claim_from_identity_providers(
            identity_providers, "siret"
        )
        if identity_providers_siret:
            additional_claims["siret"] = identity_providers_siret[0]

        return additional_claims

    def get_userinfo_claims(self, request):
        """
        Generates and saves a new JWT for this request, and returns it as the
        current user's claims.

        This is overridden to enforce JWT signing, we use `finalize_id_token` like code.
        """
        claims = super().get_userinfo_claims(request)

        header = {
            "typ": "JWT",
            "alg": request.client.algorithm,
        }
        # RS256 consumers expect a kid in the header for verifying the token
        if request.client.algorithm == AbstractApplication.RS256_ALGORITHM:
            header["kid"] = request.client.jwk_key.thumbprint()

        jwt_token = jwt.JWT(
            header=json.dumps(header, default=str),
            claims=json.dumps(claims, default=str),
        )
        jwt_token.make_signed_token(request.client.jwk_key)
        return jwt_token.serialize()
