"""Create or update the OAuth application used by OIDC load tests."""

from __future__ import annotations

from django.core.management.base import BaseCommand

from oauth2_provider.models import Application, get_application_model


class Command(BaseCommand):
    """Create a deterministic OAuth2 client for Locust scenarios."""

    help = "Create/update the OAuth client used by OIDC load tests."

    def add_arguments(self, parser):
        """Register CLI arguments."""
        parser.add_argument(
            "--client-id",
            default="oidc-test-client",
            help="OAuth client_id to create or update.",
        )
        parser.add_argument(
            "--client-secret",
            default="oidc-test-secret",
            help="OAuth client_secret to set on the application.",
        )
        parser.add_argument(
            "--redirect-uri",
            default="https://client.example.test/callback",
            help="Allowed redirect URI for authorization code flow.",
        )

    def handle(self, *args, **options):
        """Persist the load-test OAuth application in database."""
        app_model = get_application_model()

        application, created = app_model.objects.get_or_create(
            client_id=options["client_id"],
            defaults={
                "name": "OIDC Load Test Client",
                "client_secret": options["client_secret"],
                "client_type": Application.CLIENT_CONFIDENTIAL,
                "authorization_grant_type": Application.GRANT_AUTHORIZATION_CODE,
                "redirect_uris": options["redirect_uri"],
                "skip_authorization": True,
                "algorithm": Application.RS256_ALGORITHM,
            },
        )

        if not created:
            application.client_secret = options["client_secret"]
            application.redirect_uris = options["redirect_uri"]
            application.client_type = Application.CLIENT_CONFIDENTIAL
            application.authorization_grant_type = Application.GRANT_AUTHORIZATION_CODE
            application.skip_authorization = True
            application.algorithm = Application.RS256_ALGORITHM
            application.save(
                update_fields=[
                    "client_secret",
                    "redirect_uris",
                    "client_type",
                    "authorization_grant_type",
                    "skip_authorization",
                    "algorithm",
                ]
            )

        action = "created" if created else "updated"
        self.stdout.write(
            f"OAuth client {options['client_id']} {action} for OIDC load tests."
        )
