"""Load profile definitions for OIDC Locust scenarios."""

from locust import LoadTestShape

try:
    from .config import CONFIG
except ImportError:  # pragma: no cover
    from config import CONFIG


class OIDCProfileShape(LoadTestShape):
    """Optional shape controller activated via OIDC_LOADTEST_PROFILE."""

    profile_stages = {
        "smoke": [(120, 5, 1)],
        "nominal": [(600, 50, 5)],
        "peak": [(300, 200, 20)],
        "endurance": [(3600, 50, 5)],
        "mix-realistic": [(300, 20, 2), (900, 80, 8), (1200, 80, 2)],
    }

    def tick(self):
        """Return next shape stage, or None to stop when the profile ends."""
        if CONFIG.profile in ("", "manual"):
            return None

        run_time = self.get_run_time()
        elapsed = 0
        stages = self.profile_stages.get(CONFIG.profile)
        if not stages:
            return None

        for duration, users, spawn_rate in stages:
            elapsed += duration
            if run_time < elapsed:
                return (users, spawn_rate)

        return None
