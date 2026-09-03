"""Utilities for URLs."""

from urllib.parse import parse_qs, urlencode, urlsplit


def add_query_params(url: str, params: dict[str, str | list[str] | None]) -> str:
    """Add query parameters to an URL"""
    params = {k: v for k, v in params.items() if v is not None}  # Filter out None value

    url_parts = urlsplit(url)
    query = parse_qs(url_parts.query, keep_blank_values=True)
    query.update(params)
    return url_parts._replace(query=urlencode(query, doseq=True)).geturl()


def get_query_params(url: str, flatten: bool = True) -> dict[str, str | list[str]]:
    """Get the query parameters from an URL"""
    query = parse_qs(urlsplit(url).query, keep_blank_values=True)
    return (
        {k: v[0] if len(v) == 1 else v for k, v in query.items()} if flatten else query
    )
