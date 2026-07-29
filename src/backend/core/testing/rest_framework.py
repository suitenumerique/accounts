"""Testing utilities for Django REST Framework"""

from rest_framework.exceptions import ErrorDetail


def assert_errors_code(
    errors: dict[str, list[ErrorDetail]], expected_errors_code: dict[str, list[str]]
) -> None:
    """Assert that the error codes in ``errors`` are equals to ``expected_errors_code``"""

    errors_as_code = {
        field_name: [error.code for error in field_errors]
        for field_name, field_errors in errors.items()
    }
    assert errors_as_code == expected_errors_code  # noqa: S101
