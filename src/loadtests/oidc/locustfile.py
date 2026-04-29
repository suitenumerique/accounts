"""Locust entry point for OIDC authentication load tests."""

from locust import HttpUser, between, task

try:
    from .config import CONFIG
    from .profiles import OIDCProfileShape  # noqa: F401
    from .scenarios import run_existing_session_flow, run_full_e2e_new_session_flow
except ImportError:  # pragma: no cover
    from config import CONFIG
    from profiles import OIDCProfileShape  # noqa: F401
    from scenarios import run_existing_session_flow, run_full_e2e_new_session_flow


class OIDCNewSessionUser(HttpUser):
    """Virtual user representing cold logins requiring full OIDC authentication."""

    wait_time = between(0.2, 1.2)
    weight = max(CONFIG.new_session_user_weight, 1)

    @task
    def full_e2e_new_session(self) -> None:
        """Run the full flow including upstream authorize + callback + token exchange."""
        run_full_e2e_new_session_flow(user=self, config=CONFIG)


class OIDCExistingSessionUser(HttpUser):
    """Virtual user representing warm sessions already authenticated on Accounts."""

    wait_time = between(0.2, 1.2)
    weight = max(CONFIG.existing_session_user_weight, 1)

    def on_start(self) -> None:
        """Bootstrap one login so next iterations measure the active-session path."""
        run_full_e2e_new_session_flow(user=self, config=CONFIG)

    @task
    def full_e2e_existing_session(self) -> None:
        """Run authorize + token exchange while reusing current authenticated session."""
        run_existing_session_flow(user=self, config=CONFIG)
