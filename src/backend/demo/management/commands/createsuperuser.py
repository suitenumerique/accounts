"""Management user to create a superuser."""

from django.core.management.base import BaseCommand

from users.models import User


class Command(BaseCommand):
    """Management command to create a superuser from and email and password."""

    help = "Create a superuser with an email and a password"

    def add_arguments(self, parser):
        """Define required arguments "email" and "password"."""
        parser.add_argument(
            "--email",
            help=("Email for the user."),
        )
        parser.add_argument(
            "--password",
            help="Password for the user.",
        )

    def handle(self, *args, **options):
        """
        Given an email and a password, create a superuser or upgrade the existing
        user to superuser status.
        """
        email = options.get("email")
        try:
            user = User.objects.get_by_natural_key(email)
        except User.DoesNotExist:
            User.objects.create_superuser(email=email, password=options["password"])
            message = "Superuser created successfully."
        else:
            if user.is_superuser and user.is_staff:
                message = "Superuser already exists."
            else:
                user.is_superuser = True
                user.is_staff = True
                message = "User already existed and was upgraded to superuser."

            user.set_password(options["password"])
            user.save()

        self.stdout.write(self.style.SUCCESS(message))
