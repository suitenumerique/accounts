"""Authentication app's API serializers"""

from django.contrib.auth import get_user_model

from rest_framework import serializers

from core import validators as core_validators

from authentication import models


class AuthRequestSerializer(serializers.ModelSerializer):
    """Serializer for ``authentication.models.AuthRequest`` model"""

    class Meta:
        model = models.AuthRequest
        fields = ["id", "email", "expires_at"]
        read_only_fields = ["id", "expires_at"]
        extra_kwargs = {
            "email": {"write_only": True, "required": True, "allow_blank": False}
        }

    def save(self, **kwargs):
        save_data = {**self.validated_data, **kwargs}
        if "email" in save_data and "user" not in save_data:
            try:
                kwargs.update(
                    {
                        "user": get_user_model().objects.get(email=save_data["email"]),
                        "email": "",
                    }
                )
            except get_user_model().DoesNotExist:
                pass
        return super().save(**kwargs)


class AuthRequestAttemptCreateSerializer(serializers.ModelSerializer):
    """Serializer for ``authentication.models.AuthRequestAttempt`` create operation"""

    class Meta:
        model = models.AuthRequestAttempt
        fields = ["id", "strategy", "client_challenge", "expires_at"]
        read_only_fields = ["id", "expires_at"]
        extra_kwargs = {"client_challenge": {"required": True, "allow_blank": False}}


class AuthRequestAttemptRetrieveSerializer(serializers.ModelSerializer):
    """Serializer for ``authentication.models.AuthRequestAttempt`` retrieve operation"""

    class Meta:
        model = models.AuthRequestAttempt
        fields = [
            "id",
            "strategy",
            "secret",
            "fulfilled_at",
            "expires_at",
            "created_at",
        ]
        read_only_fields = fields


class AuthRequestAttemptLoginSerializer(serializers.Serializer):  # pylint: disable=abstract-method
    """Serializer for ``authentication.views.AuthRequestAttemptLoginView``"""

    secret = serializers.CharField(write_only=True)
    client_verifier = serializers.CharField(
        write_only=True, validators=[core_validators.pkce_code_verifier_validator]
    )
