"""Unit tests for our state utilities."""

import random

import pytest

from core.utils.state import SESSION_KEY, make_state_key, set_state, state_exists


def test_make_state_key(settings):
    """Test make_state_key()"""
    key_length = random.randint(1, 10)
    settings.SESSION_STATE_KEY_LENGTH = key_length

    assert len(make_state_key()) == key_length


def test_set_state(client):
    """Test set_state()"""
    provided_key = set_state(client.session, key="my-key", data={"key": "value"})
    generated_key = set_state(client.session, key=None, data="generated-key-data")
    empty_data_key = set_state(client.session)

    assert provided_key == "my-key"
    assert len({provided_key, generated_key, empty_data_key}) == 3
    assert client.session[SESSION_KEY] == {
        provided_key: {"data": {"key": "value"}},
        generated_key: {"data": "generated-key-data"},
        empty_data_key: {"data": {}},
    }


@pytest.mark.parametrize(
    "session,key,expected",
    [
        pytest.param({}, "key", False, id="no-session-key"),
        pytest.param({SESSION_KEY: {"": None}}, "", False, id="empty-key"),
        pytest.param({SESSION_KEY: {"key": None}}, "missing", False, id="missing-key"),
        pytest.param({SESSION_KEY: {"key": {"data": None}}}, "key", True, id="key"),
    ],
)
def test_state_exists(session, key, expected):
    """Test state_exists()"""
    assert state_exists(session, key) is expected
