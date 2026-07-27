"""Declare and configure the models for the accounts authentication application."""

import datetime

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from social_django.storage import DjangoUserMixin

from core.fields import TypeSafeEncryptedJSONField
from core.models import BaseModel
from core.validators import pkce_code_challenge_validator


class IdentityProviderName(models.TextChoices):
    """Enumeration of the supported Identity Provider."""

    PRO_CONNECT = "pro-connect", "ProConnect"


class IdentityProviderUser(BaseModel, DjangoUserMixin):
    """Social Auth association model customized (encrypted `extra_data`)"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="identity_providers",
        on_delete=models.CASCADE,
        verbose_name=_("user"),
    )
    provider = models.CharField(
        choices=IdentityProviderName.choices, verbose_name=_("identity provider")
    )
    uid = models.CharField(db_index=True, verbose_name=_("identity provider user id"))
    extra_data = TypeSafeEncryptedJSONField(default=dict, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["provider", "uid"],
                name="unique_identity_provider_uid_per_provider",
            ),
            models.CheckConstraint(
                condition=~models.Q(uid=""), name="identity_provider_uid_required"
            ),
        ]

    def __str__(self):
        return str(self.user)

    @classmethod
    def get_social_auth(cls, provider: str, uid: str | int):
        if not isinstance(uid, str):
            uid = str(uid)
        try:
            return cls.objects.select_related("user").get(provider=provider, uid=uid)
        except cls.DoesNotExist:
            return None

    @classmethod
    def username_max_length(cls):
        return cls.user_model()._meta.get_field(cls.username_field()).max_length  # noqa: SLF001

    @classmethod
    def user_model(cls):
        return cls._meta.get_field("user").remote_field.model


def auth_request_default_expiration():
    """Generate the default value for AuthRequest and AuthRequestAttempt's `expires_at` field"""
    return timezone.now() + datetime.timedelta(
        seconds=settings.AUTH_REQUEST_DEFAULT_DURATION
    )


class AuthRequestStrategy(models.TextChoices):
    """Enumeration of the supported auth request strategy"""

    PASSWORD = "PASSWORD", _("through its password")
    DEVICE = "DEVICE", _("through another device")


class AuthRequest(BaseModel):
    """Model to represent a user that wants, or need, to be authenticated.

    Creating an `AuthRequest()` can be seen as opening a session, but we need statelessness and
    shareability for cross-devices and out-of-band authentication, so we persist it in the
    database and will explicitly use the primary keys instead of relying on cookies.

    This model doesn't hold any information about authentication scheme as to not tie the "what"
    to the "how", especially since the "how" will change based on various conditions while the
    "what" will always be the same.
    Splitting into multiple models is also done as to properly handle ACR [1] requested from
    the OIDC Provider part of the project, and AMR [2] once successfully authenticated.

    Creation of an object with only an email is permitted as to not fail early,
    as this could be used to probe known and unknown values using iteration.

    [1] https://openid.net/specs/openid-connect-eap-acr-values-1_0.html
    [2] https://datatracker.ietf.org/doc/html/rfc8176
    """

    email = models.EmailField(blank=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="login_requests",
        verbose_name=_("user"),
    )

    expires_at = models.DateTimeField(
        default=auth_request_default_expiration,
        editable=False,
        verbose_name=_("expiration timestamp"),
        help_text=_("date and time at which the authentication request will expire"),
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(~models.Q(email=""), user=None)
                | models.Q(user__isnull=False, email=""),
                name="email_or_user",
            )
        ]

    def is_active(self):
        """Return ``True`` if the request is yet to expires"""
        return self.expires_at > timezone.now()


class AuthRequestAttempt(BaseModel):
    """Model to represent a user attempt to be authenticated.

    That model is expected to be throwable and is not designed to be reused,
    each attempt should have its own object created as to facilitate supervision and auditability.

    The `secret` can be anything and should suffice to handle all expected strategies,
    in the end authentification is (kinda) always pairing two things:
     1. An identifier: username, obfuscated or not id, token, etc.
     2. A secret: password, PIN, token, etc.

    The `client_challenge` works like how PKCE works in OIDC and is here for the same reasons,
    usually we don't need it as the identifier and the secret are sent in the same request so we
    can trust the user wanting to be authenticated is the one in possession of the device if it
    succeeds, but as we separate the identifier from the secret so we need another way to
    establish that trust.
    """

    request = models.ForeignKey(
        AuthRequest,
        on_delete=models.CASCADE,
        related_name="attempts",
        verbose_name=_("authentication request"),
    )

    strategy = models.CharField(
        choices=AuthRequestStrategy.choices,
        verbose_name=_("authentication request strategy"),
    )
    client_challenge = models.CharField(
        blank=True,
        validators=[pkce_code_challenge_validator],
        verbose_name=_("client challenge (PKCE-like)"),
    )
    secret = models.CharField(blank=True)

    fulfilled_at = models.DateTimeField(
        null=True,
        default=None,
        editable=False,
        verbose_name=_("fulfillment timestamp"),
        help_text=_("date and time at which the attempt was fulfilled"),
    )
    expires_at = models.DateTimeField(
        default=auth_request_default_expiration,
        editable=False,
        verbose_name=_("expiration timestamp"),
        help_text=_(
            "date and time at which the authentication request attempt will expire"
        ),
    )

    def is_active(self):
        """Return ``True`` if the attempt is not fulfilled and is yet to expires"""
        return not self.fulfilled_at and self.expires_at > timezone.now()

    def fulfill(self):
        """Mark the attempt as successfully fulfilled"""
        self.fulfilled_at = timezone.now()
        # FIXME: Should we also set .expires_at to .fulfilled_at as the attempt is now unusable?
        # Clear the secret and the client challenge as precaution now that they have been used
        self.secret = ""
        self.client_challenge = ""

        self.save(
            update_fields={"fulfilled_at", "secret", "client_challenge", "updated_at"}
        )
