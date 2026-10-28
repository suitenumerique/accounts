"""Pytest's conftest for the accounts project"""

import pytest

import authentication.backends

###### Hooks ######


@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(items):
    """Automatically add pytest db marker if needed."""
    for item in items:
        markers = {marker.name for marker in item.iter_markers()}
        if "no_django_db" not in markers and "django_db" not in markers:
            item.add_marker(pytest.mark.django_db)


###### Fixtures ######


@pytest.fixture(name="invalidate_psa_backends_cache")
def invalidate_psa_backends_cache_fixture():
    """Fixture that invalidate the cache set on some methods of a Social Auth's backend."""
    # The strategy and the storage don't really matter because the cache key
    # is computed with `(this.__class__, args, tuple(sorted(kwargs.items())))`
    backend = authentication.backends.ProConnect()
    backend.oidc_config.invalidate()
    backend.get_jwks_keys.invalidate()
