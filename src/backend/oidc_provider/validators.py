"""
Module for OIDC authentication.

Contains all related code for OIDC authentication flow between
Accounts and the products.
"""

import json

import oauthlib.common
from jwcrypto import jwt
from oauth2_provider.models import AbstractApplication
from oauth2_provider.oauth2_validators import OAuth2Validator


class LaSuiteValidator(OAuth2Validator):
    """
    This validator is to be used with the LaSuite projects, but can also be used
    for any project that needs to add the same claims to the token.
    It adds additional claims to support migration from ProConnect to Accounts.
    """

    oidc_claim_scope = {
        "sub": "openid",
        # Claims for "email" scope
        "email": "email",
        # "email_verified": "email",  # TODO
        # Claims for "profile" scope
        "family_name": "profile",
        "given_name": "profile",
        # Claims for "siret" scope FIXME: Maybe have a broader one, like "organization"?
        # "siret": "siret",  # TODO?
    }

    def get_discovery_claims(self, request):
        return super().get_discovery_claims(request) + list(
            self.oidc_claim_scope.keys()
        )

    def get_additional_claims(self, request: oauthlib.common.Request):
        """
        Generate additional claims to be included in the token.

        Args:
            request: The OAuth2 request object containing user and scope information.

        Returns:
            dict: A dictionary of additional claims to be included in the token.
        """
        additional_claims = super().get_additional_claims(request)

        # FIXME: To ease products migration we should use ProConnect's sub but this could go bad when adding new IdP,
        #   we also need to choose is we want to really use the email (it's our username) as this prevent modifying it
        #   which could cause us problems with some IdP...
        additional_claims["sub"] = str(request.user.get_username())

        # Include 'acr' claim if it is present in the request claims and equals 'eidas1'
        # see _create_authorization_code method for more details
        # TODO: the `acr` should be the one returned by the upstream IdP or the one enforced by accounts
        if request.claims and request.claims.get("acr") == "eidas1":
            additional_claims["acr"] = "eidas1"
        # TODO: We need to add `amr` based on upstream information or user authentication backend.
        # additional_claims["amr"] = "pwd"

        # "email" claims
        additional_claims["email"] = request.user.email
        # additional_claims["email_verified"] = ...  # TODO

        # "profile" claims
        additional_claims["given_name"] = request.user.short_name
        additional_claims["name"] = request.user.full_name

        # FIXME: .metadata is replaced by `.identity_providers`
        #  As we are going to have only one identity provider for now, and until we normalized Organizations, we could
        #  extract the needed informations directly from the stored id_token.
        # if "siret" in request.scopes:
        #     # The following line will fail on purpose if we don't have the proper information
        #     additional_claims["siret"] = request.user.metadata["siret"]
        #     additional_claims["siren"] = request.user.metadata["siret"][:9]  # FIXME: Do we need it as claims?

        return additional_claims

    def _create_authorization_code(
        self, request: oauthlib.common.Request, code, expires=None
    ):
        """
        Create an authorization code and handle 'acr_values' in the request.

        Args:
            request: The OAuth2 request object containing user and scope information.
            code: The authorization code to be created.
            expires: The expiration time of the authorization code.

        Returns:
            The created authorization code.
        """
        # If 'eidas1' is in 'acr_values', add 'acr' claim to the request claims
        # This allows the token to have this information and pass it to the /token
        # endpoint and return it in the token response
        # TODO: We need to forward the requested ACR to the upstream IdP so setting in the AS token will not be enough
        #   this is probably to be done in `.save_authorization_code()`.
        #   This should also probably be done for scopes so we don't ask everything everytime to upstream IdP.
        # Split and strip 'acr_values' from the request, if present
        acr_values = (
            [value.strip() for value in request.acr_values.split(" ")]
            if request.acr_values
            else []
        )
        if "eidas1" in acr_values:
            request.claims = request.claims or {}
            request.claims["acr"] = "eidas1"

        # Call the superclass method to create the authorization code
        return super()._create_authorization_code(request, code, expires)

    def get_userinfo_claims(self, request: oauthlib.common.Request):
        """
        Generates and saves a new JWT for this request, and returns it as the
        current user's claims.

        This is overridden to enforce JWT signing, we use `finalize_id_token` like code.
        """
        claims, _expiration_time = self.get_id_token_dictionary(
            request.access_token, None, request
        )

        # Per the specifications[1] `acr` and `amr` claims are only meaningful for the ID Token,
        # as we reuse its plumbing to create the UserInfo response we need to remove them.
        # But we could add the support of "OAuth 2.0 Step Up Authentication Challenge Protocol" [2].
        # [1] https://openid.net/specs/openid-connect-basic-1_0.html#IDToken
        # [2] https://datatracker.ietf.org/doc/html/rfc9470
        claims.pop("acr", None)
        claims.pop("amr", None)

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

    def introspect_token(self, token, token_type_hint, request, *args, **kwargs):
        """Introspect an access or refresh token.

        Called once the introspect request is validated. This method should
        verify the *token* and either return a dictionary with the list of
        claims associated, or `None` in case the token is unknown.

        Below the list of registered claims you should be interested in:

        - scope : space-separated list of scopes
        - client_id : client identifier
        - username : human-readable identifier for the resource owner
        - token_type : type of the token
        - exp : integer timestamp indicating when this token will expire
        - iat : integer timestamp indicating when this token was issued
        - nbf : integer timestamp indicating when it can be "not-before" used
        - sub : subject of the token - identifier of the resource owner
        - aud : list of string identifiers representing the intended audience
        - iss : string representing issuer of this token
        - jti : string identifier for the token

        Note that most of them are coming directly from JWT RFC. More details
        can be found in `Introspect Claims`_ or `JWT Claims`_.

        The implementation can use *token_type_hint* to improve lookup
        efficiency, but must fallback to other types to be compliant with RFC.

        The dict of claims is added to request.token after this method.
        """
        raise RuntimeError("Introspection not implemented")  # FIXME

    def validate_silent_authorization(self, request: oauthlib.common.Request):
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

    def validate_silent_login(self, request: oauthlib.common.Request):
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
