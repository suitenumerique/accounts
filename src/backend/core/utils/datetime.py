"""Utilities for date and time"""


def normalize_zero_utc_offset(value):
    """Normalize the zero UTC offset to be ``Z`` instead of ``+00:00``"""

    value = value.isoformat()
    if value.endswith("+00:00"):
        value = value.removesuffix("+00:00") + "Z"
    return value
