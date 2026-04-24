"""Parameters that define how the demo site will be built."""

NB_OBJECTS = {
    "users": 50,
}

# OAuth2 Applications for demo
OAUTH2_APPLICATIONS = [
    {
        "name": "Demo Product App",
        "client_id": "demo-product-client-id",
        "client_secret": "demo-product-secret-change-in-production",
        "redirect_uris": [
            "http://localhost:9901/api/v1.0/callback/",
        ],
        "skip_authorization": False,
    },
    {
        "name": "Test E2E App",
        "client_id": "e2e-test-client",
        "client_secret": "e2e-test-secret",
        "redirect_uris": [
            "http://localhost:8000/test/callback",
        ],
        "skip_authorization": True,  # Skip consent for E2E tests
    },
    {
        "name": "Standalone App",
        "client_id": "standalone-test-client",
        "client_secret": "standalone-test-secret",
        "redirect_uris": [
            "http://localhost:8000/test/callback",
        ],
        "skip_authorization": True,  # Skip consent for E2E tests
    },
]

DEV_USERS = [
    {"username": "accounts", "email": "accounts@accounts.world", "language": "en-us"},
    {
        "username": "user-e2e-webkit",
        "email": "user.test@webkit.test",
        "language": "en-us",
    },
    {
        "username": "user-e2e-firefox",
        "email": "user.test@firefox.test",
        "language": "en-us",
    },
    {
        "username": "user-e2e-chromium",
        "email": "user.test@chromium.test",
        "language": "en-us",
    },
]
