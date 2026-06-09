from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from encrypted_fields import EncryptedJSONField
from social_django.storage import DjangoUserMixin

from core.models import BaseModel

from authentication.backends import ProConnect


class IdentityProviderName(models.TextChoices):
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
    extra_data = EncryptedJSONField(default=dict, blank=True)

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
