"""
Core application factories
"""

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password

import factory.fuzzy
from faker import Faker

fake = Faker()


class UserFactory(factory.django.DjangoModelFactory):
    """A factory to random users for testing purposes."""

    class Meta:
        model = get_user_model()
        # Skip postgeneration save, no save is made in the postgeneration methods.
        skip_postgeneration_save = True

    sub = factory.Sequence(lambda n: f"user{n!s}")
    email = factory.Faker("email")
    full_name = factory.Faker("name")
    short_name = factory.Faker("first_name")
    language = factory.fuzzy.FuzzyChoice([lang[0] for lang in settings.LANGUAGES])
    password = make_password("password")
