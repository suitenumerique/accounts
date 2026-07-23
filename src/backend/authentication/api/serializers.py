from django.contrib.auth import get_user_model

from rest_framework import serializers

from core import validators as core_validators

from authentication import models


class AuthRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.AuthRequest
        fields = ["id", "email", "expires_at"]
        read_only_fields = ["id", "expires_at"]
        extra_kwargs = {"email": {"write_only": True}}

    def save(self, **kwargs):
        save_data = {**self.validated_data, **kwargs}
        if "email" in save_data and "user" not in save_data:
            kwargs = {
                "user": get_user_model().objects.get(email=save_data["email"]),
                "email": "",
            }
        return super().save(**kwargs)


class AuthRequestAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.AuthRequestAttempt
        fields = ["id", "strategy", "client_challenge", "expires_at"]
        read_only_fields = ["id", "expires_at"]


class AuthRequestAttemptLoginSerializer(serializers.Serializer):
    client_verifier = serializers.CharField(
        validators=[core_validators.pkce_code_verifier_validator]
    )
    secret = serializers.CharField()
