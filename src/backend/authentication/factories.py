"""
OIDC Provider factories
"""

import factory.fuzzy
from faker import Faker

from core.factories import UserFactory

from authentication.models import IdentityProviderUser

fake = Faker()


class IdentityProviderUserFactory(factory.django.DjangoModelFactory):
    """Factory for our custom Social Auth association model."""

    class Meta:
        model = IdentityProviderUser

    user = factory.SubFactory(UserFactory)
    provider = "pro-connect"
    uid = factory.Faker("uuid4")
    extra_data = factory.Dict({})
