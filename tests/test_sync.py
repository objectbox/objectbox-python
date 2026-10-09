import gc
import weakref
from typing import Callable, Optional

import pytest

from objectbox.exceptions import IllegalArgumentError
from objectbox.sync import *


def test_sync_is_available():
    # Must not raise if Sync is not available (standard library)
    assert Sync.is_available() in (True, False)


@pytest.mark.sync
def test_sync_results_without_server(sync_client):
    # Non-error "failures" are returned as values (not raised)
    assert sync_client.protocol_server_version() == 0
    assert sync_client.request_updates(True) is False
    assert sync_client.cancel_updates() is False
    assert sync_client.wait_for_logged_in_state(timeout_millis=1) is False


@pytest.mark.sync
def test_sync_protocol_version():
    version = SyncClient.protocol_version()
    assert version >= 1


@pytest.mark.sync
def test_sync_client_states(sync_client):
    assert sync_client.get_sync_state() == SyncState.CREATED
    sync_client.start()
    assert sync_client.get_sync_state() == SyncState.STARTED
    sync_client.stop()
    assert sync_client.get_sync_state() == SyncState.STOPPED


@pytest.mark.sync
def test_sync_listener(sync_server, sync_client, login_listener, connection_listener):
    if not sync_server:
        pytest.skip("Sync server not available")

    sync_client.start()
    sync_client.wait_for_logged_in_state(timeout_millis=5000)
    sync_client.stop()
    sync_client.close()

    assert login_listener.logged_in_called
    assert login_listener.login_failure_code is None
    assert connection_listener.connected_called


@pytest.mark.sync
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


@pytest.mark.sync
def test_outgoing_message_count(sync_client):
    count = sync_client.get_outgoing_message_count()
    assert count == 0

    count_limited = sync_client.get_outgoing_message_count(limit=10)
    assert count_limited == 0

    sync_client.close()

    with pytest.raises(ValueError, match='SyncClient already closed'):
        sync_client.get_outgoing_message_count()


@pytest.mark.sync
def test_multiple_credentials(sync_client):
    # empty list should raise ValueError
    with pytest.raises(ValueError, match='Provide at least one credential'):
        sync_client.set_multiple_credentials([])

    # SyncCredentials.none() is not supported with multiple credentials
    with pytest.raises(ValueError, match=r'SyncCredentials.none\(\) is not supported, use set_credentials\(\) instead'):
        sync_client.set_multiple_credentials([SyncCredentials.none()])

    sync_client.set_multiple_credentials([
        SyncCredentials.google_auth("token_google"),
        SyncCredentials.user_and_password("user1", "password"),
        SyncCredentials.shared_secret_string("secret1"),
        SyncCredentials.jwt_id_token("token1"),
        SyncCredentials.jwt_access_token("token2"),
        SyncCredentials.jwt_refresh_token("token3"),
        SyncCredentials.jwt_custom_token("token4")
    ])


@pytest.mark.sync
def test_client_closed_when_store_closed(test_store, sync_client):
    assert not sync_client.is_closed()
    test_store.close()
    assert sync_client.is_closed()


@pytest.mark.sync
def test_one_client_per_store(test_store):
    client = Sync.client(test_store, "ws://127.0.0.1:9999", SyncCredentials.none())
    with pytest.raises(ValueError, match="Only one sync client can be active for a store"):
        Sync.client_multi_urls(test_store, ["ws://127.0.0.1:9999"], SyncCredentials.none())
    client.close()
    Sync.client(test_store, "ws://127.0.0.1:9999", SyncCredentials.none()).close()


@pytest.mark.sync
def test_client_close_twice(sync_client):
    sync_client.close()
    sync_client.close()
    assert sync_client.is_closed()


@pytest.mark.sync
def test_client_on_closed_store(test_store):
    test_store.close()
    with pytest.raises(ValueError, match="Store is closed"):
        SyncClient(test_store, ["ws://127.0.0.1:9999"])


@pytest.mark.sync
def test_client_not_kept_alive_by_store(test_store):
    client = SyncClient(test_store, ["ws://127.0.0.1:9999"])
    client_ref = weakref.ref(client)
    del client
    gc.collect()
    assert client_ref() is None  # Closed via __del__
    assert len(test_store._close_listeners) == 0


@pytest.mark.sync
def assert_raises_value_error(fn: Callable[[], Optional[object]], message: Optional[str] = None):
    with pytest.raises(ValueError, match=message):
        fn()


@pytest.mark.sync
def test_client_access_after_close_throws_error(sync_client):
    sync_client.close()

    assert sync_client.is_closed()

    match_error = "SyncClient already closed"

    assert_raises_value_error(message=match_error, fn=lambda: sync_client.start())
    assert_raises_value_error(message=match_error, fn=lambda: sync_client.stop())
    assert_raises_value_error(message=match_error, fn=lambda: sync_client.get_sync_state())
    assert_raises_value_error(message=match_error, fn=lambda: sync_client.get_outgoing_message_count())
    assert_raises_value_error(message=match_error, fn=lambda: sync_client.set_credentials(SyncCredentials.none()))
    assert_raises_value_error(message=match_error,
                              fn=lambda: sync_client.set_credentials(SyncCredentials.google_auth("token_google")))
    assert_raises_value_error(message=match_error, fn=lambda: sync_client.set_multiple_credentials([
        SyncCredentials.google_auth("token_google"),
        SyncCredentials.user_and_password("user1", "password")
    ]))
    assert_raises_value_error(message=match_error,
                              fn=lambda: sync_client.set_request_updates_mode(SyncRequestUpdatesMode.AUTO))
