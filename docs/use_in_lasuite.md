# Use My Account in LaSuite

## My Account deployment

Configure OIDC provider settings:

```python
OAUTH2_PROVIDER_OIDC_RSA_PRIVATE_KEY="""-----BEGIN RSA PRIVATE KEY-----
MIIE --TRUNCATED FOR SECURITY REASONS--
-----END RSA PRIVATE KEY-----"""
```

or

```ini
OAUTH2_PROVIDER_OIDC_RSA_PRIVATE_KEY="-----BEGIN RSA PRIVATE KEY-----\nMIIE --TRUNCATED FOR SECURITY REASONS--\n-----END RSA PRIVATE KEY-----"
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

1. **Access the admin panel**: http://localhost:9901/admin/
2. **Log in** with your superuser credentials.
3. **Navigate to**: Django OAuth Toolkit > Applications > Add Application
4. **Configure**:
    - **Client id**: Leave empty for auto-generation (or set to `my-account-app`)
    - **Redirect uris**:
      ```
      http://localhost:9801/api/v1.0/oidc/callback/
      ```
    - **Client type**: `Confidential`
    - **Authorization grant type**: `Authorization code`
    - **Skip authorization**: You want to check it (probably)

### Update OIDC settings in the product

```python
# OIDC

OIDC_OP_JWKS_ENDPOINT="http://accounts:8000/api/v1.0/o/.well-known/jwks.json"
OIDC_OP_AUTHORIZATION_ENDPOINT="http://localhost:9901/api/v1.0/o/authorize/"
OIDC_OP_TOKEN_ENDPOINT="http://accounts:8000/api/v1.0/o/token/"
OIDC_OP_USER_ENDPOINT="http://accounts:8000/api/v1.0/o/userinfo/"
OIDC_OP_LOGOUT_ENDPOINT="http://accounts:8000/api/v1.0/o/logout"

OIDC_RP_CLIENT_ID="new-client-id"
OIDC_RP_CLIENT_SECRET="new-client-secret"
OIDC_RP_SIGN_ALGO="RS256"  # should be unchanged
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
