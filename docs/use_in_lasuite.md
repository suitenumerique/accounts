# Use My Account in LaSuite

## My Account deployment

Configure OIDC provider settings:

```python
OAUTH2_PROVIDER_SCOPES={
    "openid": "OpenID Connect",
    "profile": "Profile information",
    "email": "Email address",
    "given_name": "Given name",  # For backward compatibility ProConnect
    "usual_name": "Usual name",  # For backward compatibility ProConnect
    "groups": "Groups",  # Does not provide any claim for now
}
OAUTH2_PROVIDER_ACCESS_TOKEN_EXPIRE_SECONDS=3600  # 1 hour
OAUTH2_PROVIDER_REFRESH_TOKEN_EXPIRE_SECONDS=86400  # 24 hours
OAUTH2_PROVIDER_AUTHORIZATION_CODE_EXPIRE_SECONDS=300  # 5 minutes
OAUTH2_PROVIDER_OIDC_RSA_PRIVATE_KEY="""-----BEGIN RSA PRIVATE KEY-----
MIIE --TRUNCATED FOR SECURITY REASONS--
-----END RSA PRIVATE KEY-----"""
OAUTH2_PROVIDER_OAUTH2_VALIDATOR_CLASS="oidc_provider.validators.LaSuiteValidator"
OAUTH2_PROVIDER_ALLOWED_REDIRECT_URI_SCHEMES=["http", "https"]
```

or

```ini
OAUTH2_PROVIDER_SCOPES="{\"openid\": \"OpenID Connect\", \"profile\": \"Profile information\", \"email\": \"Email address\", \"given_name\": \"Given name\", \"usual_name\": \"Usual name\", \"groups\": \"Groups\"}"
OAUTH2_PROVIDER_ACCESS_TOKEN_EXPIRE_SECONDS=3600
OAUTH2_PROVIDER_REFRESH_TOKEN_EXPIRE_SECONDS=86400
OAUTH2_PROVIDER_AUTHORIZATION_CODE_EXPIRE_SECONDS=300
OAUTH2_PROVIDER_OIDC_RSA_PRIVATE_KEY="-----BEGIN RSA PRIVATE KEY-----\nMIIE --TRUNCATED FOR SECURITY REASONS--\n-----END RSA PRIVATE KEY-----"
OAUTH2_PROVIDER_OAUTH2_VALIDATOR_CLASS=oidc_provider.validators.LaSuiteValidator
OAUTH2_PROVIDER_ALLOWED_REDIRECT_URI_SCHEMES=http,https
```

Configure `OIDC_USERINFO_MANDATORY_METADATA_FIELDS`:

```python
OIDC_USERINFO_MANDATORY_METADATA_FIELDS = [
    "given_name",  # First name
    "usual_name",  # Last name
    "siret",
    "is_service_public",
    "idp_id",     # Unique identifier from the Identity Provider (e.g., fia1v2)
    "roles",      # User roles (e.g., agent_public)
]
```

or

```ini
OIDC_USERINFO_MANDATORY_METADATA_FIELDS=given_name,usual_name,siret,is_service_public,idp_id,roles
```

## First product switch (from ProConnect to My Account)

The switch from ProConnect to My Account is seamless for the user, as both products share the same SSO authentication.
However, to ensure a smooth transition, you need to update the following settings.

### Create new application in My Account

1. **Access the admin panel**: http://localhost:8000/admin/
2. **Log in** with your superuser credentials.
3. **Navigate to**: OAuth2 Provider > Applications > Add Application
4. **Configure**:
    - **Client id**: Leave empty for auto-generation (or set to `my-account-app`)
    - **User**: Select your user
    - **Redirect uris**:
      ```
      http://localhost:9901/oidc/callback
      ```
    - **Client type**: `Confidential`
    - **Authorization grant type**: `Authorization code`
    - **Scopes**: `openid email given_name usual_name profile introspection`

### Update OIDC settings in the product

```python
# OIDC

OIDC_OP_JWKS_ENDPOINT=http://host.docker.internal:9901/o/.well-known/jwks.json
OIDC_OP_AUTHORIZATION_ENDPOINT=http://localhost:9901/o/authorize/
OIDC_OP_TOKEN_ENDPOINT=http://host.docker.internal:9901/o/token/
OIDC_OP_USER_ENDPOINT=http://host.docker.internal:9901/o/userinfo/
OIDC_OP_LOGOUT_ENDPOINT=http://host.docker.internal:9901/o/logout

OIDC_RP_CLIENT_ID=new-client-id
OIDC_RP_CLIENT_SECRET=new-client-secret
OIDC_RP_SIGN_ALGO=RS256  # should be unchanged
```

For scopes, either you may keep the same scopes as before:

```python
OIDC_RP_SCOPES="openid email given_name usual_name"
OIDC_USERINFO_SHORTNAME_FIELD="given_name"
OIDC_USERINFO_FULLNAME_FIELDS="given_name,usual_name"
```

Or you can add/use the new scopes:

```python
OIDC_RP_SCOPES="openid email profile"
OIDC_USERINFO_SHORTNAME_FIELD="given_name"  # should be unchanged
OIDC_USERINFO_FULLNAME_FIELDS="name"
```
