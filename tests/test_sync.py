from collections.abc import Callable
from time import sleep

import pytest

from objectbox.exceptions import IllegalArgumentError
from objectbox.sync import *


def test_sync_protocol_version():
    version = SyncClient.protocol_version()
    assert version >= 1

def test_sync_client_states(test_store):
    server_urls = ["ws://localhost:9999"]
    client = SyncClient(test_store, server_urls)
    assert client.get_sync_state() == SyncState.CREATED
    client.start()
    assert client.get_sync_state() == SyncState.STARTED
    client.stop()
    assert client.get_sync_state() == SyncState.STOPPED
    client.close()

def test_sync_listener(test_store, login_listener, connection_listener):
    server_urls = ["ws://127.0.0.1:9999"]
    client = SyncClient(test_store, server_urls)
    client.set_credentials(SyncCredentials.shared_secret_string("shared_secret"))
    client.set_login_listener(login_listener)
    client.set_connection_listener(connection_listener)

    client.start()
    sleep(1)
    client.stop()
    client.close()

    assert login_listener.login_failure_code is not None
    assert login_listener.login_failure_code == SyncCode.CREDENTIALS_REJECTED
    assert connection_listener.connected_called
    assert connection_listener.disconnected_called


def test_filter_variables(test_store):
    server_urls = ["ws://localhost:9999"]

    filter_vars = {
        "name1": "val1",
        "name2": "val2"
    }
    client = SyncClient(test_store, server_urls, filter_vars)

    client.add_filter_variable("name3", "val3")
    client.remove_filter_variable("name1")
    client.add_filter_variable("name4", "val4")
    client.remove_all_filter_variables()

    with pytest.raises(IllegalArgumentError, match="Filter variables must have a name"):
        client.add_filter_variable("", "val5")

    client.close()


def test_outgoing_message_count(test_store):
    server_urls = ["ws://localhost:9999"]
    client = SyncClient(test_store, server_urls)

    count = client.get_outgoing_message_count()
    assert count == 0

    count_limited = client.get_outgoing_message_count(limit=10)
    assert count_limited == 0

    client.close()

    with pytest.raises(IllegalArgumentError, match='Argument "sync" must not be null'):
        client.get_outgoing_message_count()


def test_multiple_credentials(test_store):
    server_urls = ["ws://localhost:9999"]
    client = SyncClient(test_store, server_urls)

    # empty list should raise ValueError
    with pytest.raises(ValueError, match='Provide at least one credential'):
        client.set_multiple_credentials([])

    # SyncCredentials.none() is not supported with multiple credentials
    with pytest.raises(ValueError, match=r'SyncCredentials.none\(\) is not supported, use set_credentials\(\) instead'):
        client.set_multiple_credentials([SyncCredentials.none()])

    client.set_multiple_credentials([
        SyncCredentials.google_auth("token_google"),
        SyncCredentials.user_and_password("user1", "password"),
        SyncCredentials.shared_secret_string("secret1"),
        SyncCredentials.jwt_id_token("token1"),
        SyncCredentials.jwt_access_token("token2"),
        SyncCredentials.jwt_refresh_token("token3"),
        SyncCredentials.jwt_custom_token("token4")
    ])


def test_client_closed_when_store_closed(test_store):
    server_urls = ["ws://localhost:9999"]
    client = SyncClient(test_store, server_urls)

    assert not client.is_closed()
    test_store.close()
    assert client.is_closed()


def assert_raises_value_error(fn: Callable[[], object | None], message: str | None = None):
    with pytest.raises(ValueError, match=message):
        fn()


def test_client_access_after_close_throws_error(test_store):
    server_urls = ["ws://localhost:9999"]
    client = SyncClient(test_store, server_urls)
    client.close()

    assert client.is_closed()

    match_error = "SyncClient already closed"

    assert_raises_value_error(message=match_error, fn=lambda: client.start())
    assert_raises_value_error(message=match_error, fn=lambda: client.stop())
    assert_raises_value_error(message=match_error, fn=lambda: client.get_sync_state())
    assert_raises_value_error(message=match_error, fn=lambda: client.get_outgoing_message_count())
    assert_raises_value_error(message=match_error, fn=lambda: client.set_credentials(SyncCredentials.none()))
    assert_raises_value_error(message=match_error,
                              fn=lambda: client.set_credentials(SyncCredentials.google_auth("token_google")))
    assert_raises_value_error(message=match_error, fn=lambda: client.set_multiple_credentials([
        SyncCredentials.google_auth("token_google"),
        SyncCredentials.user_and_password("user1", "password")
    ]))
    assert_raises_value_error(message=match_error,
                              fn=lambda: client.set_request_updates_mode(SyncRequestUpdatesMode.AUTO))
