"""Custom validators for the core app."""

import uuid

from django.core.exceptions import ValidationError


def sub_validator(value):
    """Validate that the sub is ASCII only."""
    if not value.isascii():
        raise ValidationError("Enter a valid sub. This value should be ASCII only.")


def uuid_validator(value):
    """Validate the value is a UUID"""
    if not isinstance(value, uuid.UUID):
        try:
            uuid.UUID(value)
        except ValueError:
            raise ValidationError("Enter a valid UUID.", code="invalid") from None
