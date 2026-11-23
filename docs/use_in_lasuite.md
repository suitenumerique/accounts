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
    - **Redirect URIs**: `http://localhost:9801/api/v1.0/oidc/callback/`
    - **Client type**: `Confidential`
    - **Authorization grant type**: `Authorization code`
    - **Skip authorization**: You (probably) want to check it

### Update OIDC settings in the product

```python
# OIDC

OIDC_OP_JWKS_ENDPOINT="http://accounts:8000/api/v1.0/o/.well-known/jwks.json"
OIDC_OP_AUTHORIZATION_ENDPOINT="http://localhost:9901/api/v1.0/o/authorize/"
OIDC_OP_TOKEN_ENDPOINT="http://accounts:8000/api/v1.0/o/token/"
OIDC_OP_USER_ENDPOINT="http://accounts:8000/api/v1.0/o/userinfo/"
OIDC_OP_LOGOUT_ENDPOINT="http://localhost:9901/api/v1.0/o/logout/"

OIDC_RP_CLIENT_ID="new-client-id"  # i.e: `my-account-app`
OIDC_RP_CLIENT_SECRET="new-client-secret"
OIDC_RP_SIGN_ALGO="RS256"  # should be unchanged

# Proactively enable PKCE as this will become required at some point
OIDC_USE_PKCE=True
OIDC_PKCE_CODE_CHALLENGE_METHOD="S256"  # Default for mozilla-django-oidc

# sub **will** changes so we need email fallback and `sub` field mutability enabled.
# This is currently the "default" but "Explicit is better than implicit".
OIDC_FALLBACK_TO_EMAIL_FOR_IDENTIFICATION=True
OIDC_USER_SUB_FIELD_IMMUTABLE=False
```

For scopes, replace `given_name` and `usual_name` by `profile`:

```python
OIDC_RP_SCOPES="openid email profile"
OIDC_USERINFO_SHORTNAME_FIELD="given_name"  # should be unchanged
OIDC_USERINFO_FULLNAME_FIELDS="name"
```

If you need the `siret` claim, use the `organization` scope:

```python
OIDC_RP_SCOPES="openid organization"
```

If you need the ProConnect roles (e.g. to filter access), use the `proconnect` scope.
They are returned in the `proconnect:roles` claim.

```python
OIDC_RP_SCOPES="openid proconnect"
```

### Introspecting tokens

If you plan to introspect tokens you will need the `introspection` scope:

```python
OIDC_RP_SCOPES="openid introspection"
```

The URL should be something like `http://accounts:8000/api/v1.0/o/introspect/`.


### Resource server

To ease migration, and if it is configured, when introspecting a token not issued by _accounts_
the endpoint will call the configured upstream Identity Providers.
Note that the response will be modified according to those rules:

```json
{
   "active": "copied as is",
   "sub": "changed to match the accounts sub",
   "scope": "filtered against a whitelist",
   "client_id": "copied as is",
   "aud": "copied as is"
}
```

#### lasuite.oidc_resource_server.backend.ResourceServerBackend

Not much need to be changed:

```python
OIDC_OP_URL="http://accounts:8000/api/v1.0/o"
OIDC_RS_CLIENT_ID="new-client-id"  # Same as OIDC_RP_CLIENT_ID
OIDC_RS_CLIENT_SECRET="new-client-secret"  # Same as OIDC_RP_CLIENT_SECRET
OIDC_RS_ALLOWED_AUDIENCES="..."  # should be unchanged, they can be ProConnect and/or accounts values
```

If something other than `openid` is used in `OIDC_RS_SCOPES` then the desired scopes need to be added to the
`OAUTH2_PROVIDER_INTROSPECTION_PSA_BACKEND_FALLBACK_PASSTHROUGH_SCOPES` list of the accounts instance.

#### lasuite.oidc_resource_server.backend.JWTResourceServerBackend

> ⚠️ **Warning** Not yet supported

### Importing the existing users

A product which knows its users by their ProConnect sub can replace them by
_accounts_ subs, without waiting for each user to log in. It sends its users by
batches to `http://accounts:8000/api/v1.0/o/users-import/`, authenticated as
the application: its `client_id` and `client_secret` in an HTTP Basic
`Authorization` header. A user's access token (`Bearer`) is not accepted.
In the _accounts_ admin, the policy of the product's application must allow it to
"import users". Uncheck it once the import is done.

```http
POST /api/v1.0/o/users-import/
Authorization: Basic base64(client_id:client_secret)
Content-Type: application/json

{
  "users": [{"pk": "product-user-id", "sub": "proconnect-or-accounts-sub", "email": "user@example.com"}]
}
```

Add `"dry_run": true` to report what would be created, without writing. Omitted
or `false`, the users are imported. Any other value is refused with a `400`.

Each sub is matched, in this order, with an _accounts_ sub, then with a ProConnect sub
already known by _accounts_. The email is never used to match a user, as ProConnect
may return former emails. An unknown sub creates an _accounts_ user, with the email
as a starting value: it is updated at the first login. These users have the `import`
source, to find them if they never log in.

```json
{
  "counts": {"accounts": 1},
  "results": [
    {"pk": "product-user-id", "sub": "proconnect-or-accounts-sub", "status": "accounts", "accounts_sub": "..."}
  ]
}
```

| `status`            | Meaning                                                         | `accounts_sub` |
|---------------------|-----------------------------------------------------------------|----------------|
| `accounts`          | The sub is already an _accounts_ sub                            | the same sub   |
| `identity_provider` | The ProConnect sub of an _accounts_ user                        | its sub        |
| `created`           | Unknown sub, the user was created                               | its new sub    |
| `to_create`         | Unknown sub, the user would be created (dry run only)           | `null`         |
| `email_conflict`    | Unknown sub, but its email belongs to another _accounts_ user   | `null`         |
| `ambiguous`         | The _accounts_ sub of a user and the ProConnect sub of another  | `null`         |
| `invalid`           | The row has no valid `sub` or `email`                           | `null`         |

Several rows may get the same `accounts_sub`: they are duplicates the product decides
how to merge. A deactivated _accounts_ user is matched too: the product gets its sub,
but this user cannot log in.

The size of a batch is only limited by the size of the request body
(`DATA_UPLOAD_MAX_MEMORY_SIZE`): _accounts_ creates the users by chunks, one
transaction each. When a request fails midway, the users of the chunks already
created stay created. Importing a batch again returns the same subs, so send it again:
the users already created come back as `identity_provider`. A `409` response means a
concurrent import or login created some of the users first.
