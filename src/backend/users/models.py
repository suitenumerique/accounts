"""
Declare and configure the models for the accounts users application
"""

from logging import getLogger

from django.conf import settings
from django.contrib.auth import models as auth_models
from django.contrib.auth.base_user import AbstractBaseUser
from django.db import models
from django.utils.translation import gettext_lazy as _

from timezone_field import TimeZoneField

from core import models as core_models
from core.validators import sub_validator

logger = getLogger(__name__)


class UserManager(core_models.UserManager):
    """Custom manager for User model."""

    # pylint: disable=arguments-differ

    @classmethod
    def normalize_email(cls, email):
        # `.normalize_email()` only lower the domain part which would allow creating
        # duplicate email value, we *really* don't want that so lower everything.
        return super().normalize_email(email).lower()

    def get_by_natural_key(self, username):
        return self.get(email__iexact=username)

    def _create_user(self, email, password, **extra_fields):
        """
        Create and save a user with the given username, email, and password.
        """
        if not email:
            raise ValueError("Users must have an email address")

        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)

        return self._create_user(email, password, **extra_fields)

    create_user.alters_data = True

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email, password, **extra_fields)

    create_superuser.alters_data = True


class User(AbstractBaseUser, core_models.BaseModel, auth_models.PermissionsMixin):
    """User model to work with OIDC only authentication."""

    sub = models.CharField(
        _("sub"),
        help_text=_("Required. 255 characters or fewer. ASCII characters only."),
        max_length=255,
        validators=[sub_validator],
        unique=True,
        blank=True,
        null=True,
    )

    full_name = models.CharField(_("full name"), max_length=100, default="", blank=True)
    short_name = models.CharField(
        _("short name"),
        max_length=100,
        default="",
        blank=True,
    )

    email = models.EmailField(_("email address"), unique=True)

    language = models.CharField(
        max_length=10,
        choices=settings.LANGUAGES,
        default=None,
        verbose_name=_("language"),
        help_text=_("The language in which the user wants to see the interface."),
        null=True,
        blank=True,
    )
    timezone = TimeZoneField(
        choices_display="WITH_GMT_OFFSET",
        use_pytz=False,
        default=settings.TIME_ZONE,
        help_text=_("The timezone in which the user wants to see times."),
    )
    is_device = models.BooleanField(
        _("device"),
        default=False,
        help_text=_("Whether the user is a device or a real user."),
    )
    is_staff = models.BooleanField(
        _("staff status"),
        default=False,
        help_text=_("Whether the user can log into this admin site."),
    )
    is_active = models.BooleanField(
        _("active"),
        default=True,
        help_text=_(
            "Whether this user should be treated as active. "
            "Unselect this instead of deleting accounts."
        ),
    )

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        db_table = "accounts_user"
        verbose_name = _("user")
        verbose_name_plural = _("users")

    def __str__(self):
        return self.email or str(self.id)
