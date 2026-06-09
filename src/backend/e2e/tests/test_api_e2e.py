"""
Test e2e API endpoints.
"""

import importlib

from django.urls import clear_url_caches

import pytest
from rest_framework.test import APIClient

from core import models

import accounts.urls

pytestmark = pytest.mark.django_db


def reload_urls():
    """Reload URL patterns after changing LOAD_E2E_URLS."""
    clear_url_caches()
    importlib.reload(accounts.urls)


@pytest.fixture(autouse=True)
def reset_e2e_urls(settings):
    """Ensure e2e URLs are disabled again after each test."""
    settings.LOAD_E2E_URLS = False
    reload_urls()
    yield
    settings.LOAD_E2E_URLS = False
    reload_urls()


def enable_e2e_urls(settings):
    """Enable e2e URLs for the current test."""
    settings.LOAD_E2E_URLS = True
    reload_urls()


def test_api_e2e_user_auth_no_urls():
    """E2E URLs should return 404 unless explicitly enabled."""
    client = APIClient()

    response = client.post("/api/v1.0/e2e/user-auth/", {"email": "test@example.com"})

    assert response.status_code == 404


def test_api_e2e_user_auth_anonymous(settings):
    """Anonymous users should be allowed to create and login a user in e2e mode."""
    enable_e2e_urls(settings)
    client = APIClient()

    response = client.get("/api/v1.0/users/me/")
    assert response.status_code == 401

    response = client.post("/api/v1.0/e2e/user-auth/", {"email": "test@example.com"})
    assert response.status_code == 200
    assert response.json() == {"email": "test@example.com"}
    assert models.User.objects.filter(email="test@example.com").exists()

    response = client.get("/api/v1.0/users/me/")
    assert response.status_code == 200
    assert response.json()["email"] == "test@example.com"


def test_api_e2e_user_auth_authenticated(settings):
    """Authenticated users should be allowed to login as a new e2e user."""
    enable_e2e_urls(settings)
    client = APIClient()

    response = client.post("/api/v1.0/e2e/user-auth/", {"email": "test@example.com"})
    assert response.status_code == 200
    assert response.json() == {"email": "test@example.com"}

    response = client.post("/api/v1.0/e2e/user-auth/", {"email": "test2@example.com"})
    assert response.status_code == 200
    assert response.json() == {"email": "test2@example.com"}

    response = client.get("/api/v1.0/users/me/")
    assert response.status_code == 200
    assert response.json()["email"] == "test2@example.com"


def test_api_e2e_user_auth_email_required(settings):
    """Email is required to use the e2e auth endpoint."""
    enable_e2e_urls(settings)
    client = APIClient()

    response = client.post("/api/v1.0/e2e/user-auth/", {})

    assert response.status_code == 400
    assert response.json() == {"email": ["This field is required."]}
