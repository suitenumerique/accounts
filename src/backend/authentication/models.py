"""Declare and configure the models for the accounts authentication application."""

import datetime
import secrets

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from social_django.storage import DjangoUserMixin

from core.fields import TypeSafeEncryptedJSONField
from core.models import BaseModel
from core.standards import rfc7636
from core.validators import pkce_code_challenge_validator

from authentication.backends import ProConnect


class IdentityProviderName(models.TextChoices):
    """Enumeration of the supported Identity Provider."""

    PRO_CONNECT = ProConnect.name, ProConnect.__name__


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
    return timezone.now() + datetime.timedelta(
        seconds=settings.AUTH_REQUEST_DEFAULT_DURATION
    )


class AuthRequestStrategy(models.TextChoices):
    PASSWORD = "PASSWORD", _("through its password")
    DEVICE = "DEVICE", _("through another device")


class AuthRequest(BaseModel):
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
        return self.expires_at > timezone.now()


class AuthRequestAttempt(BaseModel):
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
        return not self.fulfilled_at and self.expires_at > timezone.now()

    def fulfill(self, secret, client_verifier):
        if not self.is_active():
            return False
        # FIXME: Should we kill the attempt on erroneous client_verifier or secret? I think it safe to not to:
        #  - this could be used for griefing and prevent a legitimate user to log in
        #  - the (relatively) short expiration timestamp reduce brute force windows, especially with a rate limit
        if not rfc7636.verify_code_verifier(client_verifier, self.client_challenge):
            return False

        if self.strategy == AuthRequestStrategy.PASSWORD:
            # Call AbstractBaseUser.check_password() so Django handle hash regeneration/hardening
            if not self.request.user.check_password(secret):
                return False
        elif not secrets.compare_digest(secret, self.secret):
            return False

        self.fulfilled_at = timezone.now()
        # FIXME: Should we clear the client_challenge and secret on success? Probably.
        self.save(update_fields={"fulfilled_at", "updated_at"})
        return True
