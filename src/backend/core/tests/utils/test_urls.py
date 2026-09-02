"""Unit tests for our URLs utilities."""

import pytest

from core.utils.urls import add_query_params, get_query_params


@pytest.mark.parametrize(
    "url,params,expected",
    [
        pytest.param(
            "http://localhost/",
            {"key": "value"},
            "http://localhost/?key=value",
            id="add-value",
        ),
        pytest.param(
            "http://localhost/?key=old",
            {"key": "new"},
            "http://localhost/?key=new",
            id="update-value",
        ),
        pytest.param(
            "http://localhost/", {"key": None}, "http://localhost/", id="none-value"
        ),
        pytest.param(
            "http://localhost/path?key=",
            {"key2": ""},
            "http://localhost/path?key=&key2=",
            id="blank-value",
        ),
        pytest.param("/", {"key": "value"}, "/?key=value", id="relative-url"),
        pytest.param(
            "/", {"key": ["value", "value2"]}, "/?key=value&key=value2", id="list-value"
        ),
    ],
)
def test_add_query_params(url, params, expected):
    """Test add_query_params()"""
    assert add_query_params(url, params) == expected


@pytest.mark.parametrize(
    "url,expected",
    [
        pytest.param("/?key=value", {"key": "value"}, id="value"),
        pytest.param("/?key=", {"key": ""}, id="empty"),
        pytest.param("/?key=value&key2=", {"key": "value", "key2": ""}, id="multiple"),
        pytest.param("/?key=value&key=value2", {"key": ["value", "value2"]}, id="list"),
        pytest.param(
            "http://localhost/path?key=value", {"key": "value"}, id="absolute"
        ),
    ],
)
def test_get_query_params(url, expected):
    """Test get_query_params()"""
    assert get_query_params(url) == expected
