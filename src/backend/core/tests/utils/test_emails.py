"""Unit tests for our email utilities."""

from core.utils.emails import normalize_email


def test_normalize_email():
    """The "normalize_email" function should strip and lowercase ASCII letters only."""
    assert normalize_email("  John.Doe@Example.COM ") == "john.doe@example.com"
    assert normalize_email("Dısk@Example.com") == "dısk@example.com"
    assert normalize_email("Diſk@Example.com") == "diſk@example.com"
    assert normalize_email("DisK@Example.com") == "disK@example.com"
    assert normalize_email("Élise@Example.com") == "Élise@example.com"
    assert normalize_email("") == ""
    assert normalize_email(None) == ""
