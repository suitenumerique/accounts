"""Fixtures for the authentication test suite."""

import pytest
from social_core.tests.models import TestStorage
from social_core.tests.strategy import TestStrategy

from authentication.backends import ProConnect


@pytest.fixture(name="reset_psa_backend_cache", autouse=True)
def reset_psa_backends_cache_fixture():
    """Fixture that reset the cache set on some methods of a Social Auth's backend."""
    backend = ProConnect(TestStrategy(TestStorage))
    backend.oidc_config.invalidate()
    backend.get_jwks_keys.invalidate()
