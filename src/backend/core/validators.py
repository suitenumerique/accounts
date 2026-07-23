"""Custom validators for the core app."""

from django.core import validators
from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext_lazy

from core.standards import rfc3986


def sub_validator(value):
    """Validate that the sub is ASCII only."""
    if not value.isascii():
        raise ValidationError("Enter a valid sub. This value should be ASCII only.")


@deconstructible
class CharactersValidator:  # noqa: PLW1641
    """Validate that the string only contain a set of characters."""

    message = ngettext_lazy(
        "That character is not allowed: %(characters_found)s.",
        "Those characters are not allowed: %(characters_found)s.",
        "count",
    )
    code = "not_allowed_characters"
    allowed_characters = ""

    def __init__(self, allowed_characters):
        self.allowed_characters = allowed_characters

    def __call__(self, value):
        if characters_found := set(value) - set(self.allowed_characters):
            raise ValidationError(
                self.message,
                code=self.code,
                params={
                    "value": value,
                    "characters_found": ",".join(sorted(characters_found)),
                    "count": len(characters_found),
                },
            )

    def __eq__(self, other):
        return (
            isinstance(other, self.__class__)
            and self.message == other.message
            and self.code == other.code
            and self.allowed_characters == other.allowed_characters
        )


@deconstructible
class URIUnreservedCharactersValidator(CharactersValidator):
    """Validate that the string only contain URI's unreserved characters.

    https://www.rfc-editor.org/info/rfc3986/#section-2.3
    """

    message = _(
        "Only URI's unreserved characters are allowed. Found: %(characters_found)s."
    )
    code = "only_uri_unreserved_characters"

    def __init__(self):
        super().__init__(rfc3986.UNRESERVED_CHARACTERS)


def pkce_code_verifier_validator(value):
    """Validate the format of a PKCE code_verifier.

    https://www.rfc-editor.org/info/rfc7636/#section-4.1
    """
    validators.MinLengthValidator(43)(value)
    validators.MaxLengthValidator(128)(value)
    URIUnreservedCharactersValidator()(value)


def pkce_code_challenge_validator(value):
    """Validate the format of a PKCE code_challenge.

    https://www.rfc-editor.org/info/rfc7636/#section-4.2
    """
    # Same validation rules than the code verifier because of the "plain" code challenge method
    pkce_code_verifier_validator(value)
