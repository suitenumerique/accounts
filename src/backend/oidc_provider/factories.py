"""
OIDC Provider factories
"""

import factory.fuzzy
from faker import Faker
from oauth2_provider.models import Application, get_application_model

fake = Faker()


CLIENT_ID = "oidc-test-client"
CLIENT_SECRET = "oidc-test-secret"  # noqa: S105
REDIRECT_URI = "https://client.example.test/callback"


class ApplicationFactory(factory.django.DjangoModelFactory):
    """Factory for OAuth2 applications used in tests."""

    class Meta:
        model = get_application_model()

    name = factory.Sequence(lambda n: f"OIDC Test App {n!s}")
    client_id = factory.Sequence(lambda n: f"oidc-test-client-{n!s}")
    client_secret = factory.Sequence(lambda n: f"oidc-test-secret-{n!s}")
    client_type = Application.CLIENT_CONFIDENTIAL
    authorization_grant_type = Application.GRANT_AUTHORIZATION_CODE
    redirect_uris = factory.Faker("uri")
    algorithm = Application.RS256_ALGORITHM
    skip_authorization = True

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Create and validate the application before saving it."""
        manager = cls._get_manager(model_class)
        application = model_class(*args, **kwargs)
        application.clean()
        application.save(using=manager.db)
        return application


class SimpleApplicationFactory(ApplicationFactory):
    """Factory for OAuth2 applications used in tests."""

    client_id = CLIENT_ID
    client_secret = CLIENT_SECRET
    redirect_uris = REDIRECT_URI
