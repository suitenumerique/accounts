"""Utilities to handle email addresses."""

import string

_ASCII_LOWERCASE_TABLE = str.maketrans(string.ascii_uppercase, string.ascii_lowercase)


def normalize_email(email):
    """Strip an email and lowercase its ASCII letters only.

    Emails are stored in this form and compared exactly.
    """
    return (email or "").strip().translate(_ASCII_LOWERCASE_TABLE)
