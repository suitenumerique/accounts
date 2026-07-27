"""
OIDC Provider factories
"""

from django.utils import timezone

import factory.fuzzy
from faker import Faker

from core.factories import UserFactory

from authentication import models

fake = Faker()


class IdentityProviderUserFactory(factory.django.DjangoModelFactory):
    """Factory for our custom Social Auth association model."""

    class Meta:
        model = models.IdentityProviderUser

    user = factory.SubFactory(UserFactory)
    provider = "pro-connect"
    uid = factory.Faker("uuid4")
    extra_data = factory.Dict({})


class AuthRequestFactory(factory.django.DjangoModelFactory):
    """Factory for ``AuthRequest``"""

    class Meta:
        model = models.AuthRequest

    class Params:  # pylint: disable=missing-class-docstring
        with_email = factory.Trait(
            user=None,
            email=factory.Faker("email"),
        )
        expired = factory.Trait(expires_at=factory.LazyFunction(timezone.now))

    user = factory.SubFactory(UserFactory)


class AuthRequestAttemptFactory(factory.django.DjangoModelFactory):
    """Factory for ``AuthRequestAttempt``"""

    class Meta:
        model = models.AuthRequestAttempt

    class Params:  # pylint: disable=missing-class-docstring
        expired = factory.Trait(expires_at=factory.LazyFunction(timezone.now))
        fulfilled = factory.Trait(
            fulfilled_at=factory.LazyFunction(timezone.now),
            secret="",
            client_challenge="",
        )

    request = factory.SubFactory(AuthRequestFactory)
    strategy = factory.Iterator(models.AuthRequestStrategy)
