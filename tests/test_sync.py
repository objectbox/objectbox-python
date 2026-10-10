import gc
import os
import shutil
import threading
import uuid
import weakref
from typing import Callable, Optional

import pytest

from objectbox import Store
from objectbox.exceptions import IllegalArgumentError
from objectbox.sync import *
from tests.common import NO_SYNC_SERVER_URL, SYNC_MODEL_JSON_FILE
from tests.model import SyncTestEntity


def test_sync_is_available():
    # Must not raise if Sync is not available (standard library)
    assert Sync.is_available() in (True, False)


@pytest.mark.sync
def test_sync_results_without_server(sync_client):
    # Non-error "failures" are returned as values (not raised)
    assert sync_client.protocol_version_server() == 0
    assert sync_client.request_updates(True) is False
    assert sync_client.cancel_updates() is False
    assert sync_client.wait_for_logged_in_state(timeout_millis=1) is False


@pytest.mark.sync
def test_request_updates_mode(sync_client):
    for mode in SyncRequestUpdatesMode:
        sync_client.set_request_updates_mode(mode)
    with pytest.raises(ValueError):
        sync_client.set_request_updates_mode("manual")


@pytest.mark.sync
def test_request_updates_manual(sync_server, test_store):
    client = Sync.client(test_store, sync_server.url, SyncCredentials.none())
    client.set_request_updates_mode(SyncRequestUpdatesMode.MANUAL)
    client.start()
    assert client.wait_for_logged_in_state(timeout_millis=5000)
    assert client.request_updates(subscribe_for_future_pushes=True)
    assert client.cancel_updates()
    assert client.request_updates(subscribe_for_future_pushes=False)
    client.close()


@pytest.mark.sync
def test_sync_protocol_version():
    version = SyncClient.protocol_version()
    assert version >= 1


@pytest.mark.sync
def test_sync_client_states(sync_client):
    assert sync_client.state() == SyncState.CREATED
    sync_client.start()
    assert sync_client.state() == SyncState.STARTED
    sync_client.stop()
    assert sync_client.state() == SyncState.STOPPED


class CompletedListener(SyncCompletedListener):
    def __init__(self):
        self.completed = threading.Event()

    def on_updates_completed(self):
        self.completed.set()


@pytest.mark.sync
def test_sync_listener(sync_server, test_store, login_listener, connection_listener):
    sync_client = Sync.client(test_store, sync_server.url, SyncCredentials.none())
    sync_client.set_login_listener(login_listener)
    sync_client.set_connection_listener(connection_listener)
    completed_listener = CompletedListener()
    sync_client.set_completed_listener(completed_listener)
    sync_client.start()
    assert sync_client.wait_for_logged_in_state(timeout_millis=5000)
    assert sync_client.protocol_version_server() >= 1
    assert completed_listener.completed.wait(timeout=5)
    sync_client.stop()
    sync_client.close()

    assert login_listener.logged_in_called
    assert login_listener.login_failure_code is None
    assert connection_listener.connected_called


@pytest.mark.sync
def test_sync_listener_removed(sync_server, test_store, login_listener, connection_listener, error_listener):
    sync_client = Sync.client(test_store, sync_server.url, SyncCredentials.none())
    sync_client.set_login_listener(login_listener)
    sync_client.set_connection_listener(connection_listener)
    completed_listener = CompletedListener()
    sync_client.set_completed_listener(completed_listener)
    sync_client.set_error_listener(error_listener)
    sync_client.set_change_listener(ChangeCollector())
    # None removes the listeners
    sync_client.set_login_listener(None)
    sync_client.set_connection_listener(None)
    sync_client.set_completed_listener(None)
    sync_client.set_error_listener(None)
    sync_client.set_change_listener(None)
    sync_client.start()
    assert sync_client.wait_for_logged_in_state(timeout_millis=5000)
    assert not completed_listener.completed.wait(timeout=0.5)
    sync_client.close()

    assert not login_listener.logged_in_called
    assert not connection_listener.connected_called


def open_sync_test_store(name: str) -> Store:
    db_dir = "testdata-" + name
    if os.path.exists(db_dir):
        shutil.rmtree(db_dir)
    os.makedirs(db_dir)
    # Copy the model JSON file (shared with the server): the store (re-)writes it
    model_json_file = os.path.join(db_dir, "objectbox-model.json")
    shutil.copyfile(SYNC_MODEL_JSON_FILE, model_json_file)
    return Store(model="sync-test", directory=db_dir, model_json_file=model_json_file)


class ChangeCollector(SyncChangeListener):
    def __init__(self):
        self.put_ids_by_entity_id = {}
        self.condition = threading.Condition()

    def on_change(self, sync_changes):
        with self.condition:
            for change in sync_changes:
                self.put_ids_by_entity_id.setdefault(change.entity_id, set()).update(change.puts)
            self.condition.notify_all()

    def wait_for(self, predicate: Callable[[], bool], timeout_seconds: float) -> bool:
        """Waits until the predicate is true, checking it after each change."""
        with self.condition:
            return self.condition.wait_for(predicate, timeout=timeout_seconds)


@pytest.mark.sync
def test_sync_data(sync_server):
    """Syncs an object from one client to another via the server."""
    store1 = open_sync_test_store("sync1")
    store2 = open_sync_test_store("sync2")
    try:
        client1 = Sync.client(store1, sync_server.url, SyncCredentials.none())
        client2 = Sync.client(store2, sync_server.url, SyncCredentials.none())
        change_collector = ChangeCollector()
        client2.set_change_listener(change_collector)
        client1.start()
        client2.start()
        assert client1.wait_for_logged_in_state(timeout_millis=5000)
        assert client2.wait_for_logged_in_state(timeout_millis=5000)

        text = "synced " + str(uuid.uuid4())  # An external server may have objects from previous runs
        store1.box(SyncTestEntity).put(SyncTestEntity(text=text))

        # Note: object IDs are local to each store (the server maps them), so find the object by its text
        def received():
            put_ids = change_collector.put_ids_by_entity_id.get(SyncTestEntity._id, ())
            return any(obj.text == text for obj in store2.box(SyncTestEntity).get_many(list(put_ids)) if obj)

        assert change_collector.wait_for(received, timeout_seconds=10)
    finally:
        store1.close()  # Also closes the sync clients
        store2.close()


@pytest.mark.sync
def test_filter_variables(test_store):
    filter_vars = {
        "name1": "val1",
        "name2": "val2"
    }
    client = SyncClient(test_store, [NO_SYNC_SERVER_URL], filter_vars)

    client.put_filter_variable("name3", "val3")
    client.remove_filter_variable("name1")
    client.put_filter_variable("name4", "val4")
    client.remove_all_filter_variables()
    client.apply_filter_variables()  # Not logged in: used with the next login

    with pytest.raises(IllegalArgumentError, match="Filter variables must have a name"):
        client.put_filter_variable("", "val5")

    client.close()


@pytest.mark.sync
def test_outgoing_message_count(sync_client):
    count = sync_client.outgoing_message_count()
    assert count == 0

    count_limited = sync_client.outgoing_message_count(limit=10)
    assert count_limited == 0

    sync_client.close()

    with pytest.raises(ValueError, match='SyncClient already closed'):
        sync_client.outgoing_message_count()


@pytest.mark.sync
def test_multiple_credentials(sync_client):
    # empty list should raise ValueError
    with pytest.raises(ValueError, match='Provide at least one credential'):
        sync_client.set_credentials([])

    # A list with a single element is fine, also SyncCredentials.none()
    sync_client.set_credentials([SyncCredentials.none()])
    sync_client.set_credentials([SyncCredentials.jwt_id_token("token")])

    # Invalid elements are detected before adding any credentials;
    # SyncCredentials.none() is not supported with multiple credentials
    with pytest.raises(ValueError, match=r'SyncCredentials.none\(\) is not supported with multiple credentials'):
        sync_client.set_credentials([SyncCredentials.google_auth("token"), SyncCredentials.none()])
    with pytest.raises(TypeError, match='Unsupported credentials'):
        sync_client.set_credentials([SyncCredentials.google_auth("token"), "token"])
    with pytest.raises(TypeError, match='Unsupported credentials'):
        sync_client.set_credentials("token")

    sync_client.set_credentials([
        SyncCredentials.google_auth("token_google"),
        SyncCredentials.user_and_password("user1", "password"),
        SyncCredentials.shared_secret("secret1"),
        SyncCredentials.shared_secret(b"\x00\x2e\x4f\xc1"),
        SyncCredentials.jwt_id_token("token1"),
        SyncCredentials.jwt_access_token("token2"),
        SyncCredentials.jwt_refresh_token("token3"),
        SyncCredentials.jwt_custom_token("token4")
    ])


def test_credentials_str_or_bytes():
    assert SyncCredentials.shared_secret("secret").secret == b"secret"
    assert SyncCredentials.shared_secret(b"\x00\xff").secret == b"\x00\xff"
    assert SyncCredentials.google_auth(bytearray(b"token")).secret == b"token"
    with pytest.raises(TypeError, match="Expected str or bytes"):
        SyncCredentials.shared_secret(42)


@pytest.mark.sync
def test_client_closed_when_store_closed(test_store, sync_client):
    assert not sync_client.is_closed()
    test_store.close()
    assert sync_client.is_closed()


@pytest.mark.sync
def test_login_failure_code(test_store, login_listener):
    client = SyncClient(test_store, [NO_SYNC_SERVER_URL])
    client.set_login_listener(login_listener)
    # Call the C callback directly (would require a server rejecting the login)
    c_login_failure_listener = client._SyncClient__c_callbacks[1]
    c_login_failure_listener(None, SyncCode.CREDENTIALS_REJECTED)
    assert login_listener.login_failure_code is SyncCode.CREDENTIALS_REJECTED
    c_login_failure_listener(None, 12345)  # Unknown code
    assert login_listener.login_failure_code == 12345
    client.close()


@pytest.mark.sync
def test_sync_error(test_store, error_listener):
    client = SyncClient(test_store, [NO_SYNC_SERVER_URL])
    client.set_error_listener(error_listener)
    # Call the C callback directly (would require a server rejecting a TX)
    c_error_listener = client._SyncClient__c_callbacks[0]
    c_error_listener(None, SyncError.REJECT_TX_NO_PERMISSION)
    assert error_listener.sync_error is SyncError.REJECT_TX_NO_PERMISSION
    c_error_listener(None, 12345)  # Unknown error
    assert error_listener.sync_error == 12345
    client.close()


@pytest.mark.sync
def test_one_client_per_store(test_store):
    client = Sync.client(test_store, NO_SYNC_SERVER_URL, SyncCredentials.none())
    with pytest.raises(ValueError, match="Only one sync client can be active for a store"):
        Sync.client(test_store, [NO_SYNC_SERVER_URL], SyncCredentials.none())
    client.close()
    Sync.client(test_store, NO_SYNC_SERVER_URL, SyncCredentials.none()).close()


@pytest.mark.sync
def test_client_multiple_urls_and_credentials(test_store):
    client = Sync.client(test_store, [NO_SYNC_SERVER_URL, NO_SYNC_SERVER_URL + "1"],
                         [SyncCredentials.jwt_id_token("token"), SyncCredentials.user_and_password("user", "pw")],
                         filter_variables={"name": "value"})
    assert client.state() == SyncState.CREATED
    client.close()


@pytest.mark.sync
def test_client_closed_if_credentials_fail(test_store):
    with pytest.raises(TypeError, match='Unsupported credentials'):
        Sync.client(test_store, NO_SYNC_SERVER_URL, "token")
    # The failed client is closed, i.e. not active for the store
    Sync.client(test_store, NO_SYNC_SERVER_URL, SyncCredentials.none()).close()


@pytest.mark.sync
def test_client_close_twice(sync_client):
    sync_client.close()
    sync_client.close()
    assert sync_client.is_closed()


@pytest.mark.sync
def test_client_on_closed_store(test_store):
    test_store.close()
    with pytest.raises(ValueError, match="Store is closed"):
        SyncClient(test_store, [NO_SYNC_SERVER_URL])


@pytest.mark.sync
def test_client_not_kept_alive_by_store(test_store):
    client = SyncClient(test_store, [NO_SYNC_SERVER_URL])
    client_ref = weakref.ref(client)
    del client
    gc.collect()
    assert client_ref() is None  # Closed via __del__
    assert len(test_store._close_listeners) == 0


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
    assert_raises_value_error(message=match_error, fn=lambda: sync_client.state())
    assert_raises_value_error(message=match_error, fn=lambda: sync_client.outgoing_message_count())
    assert_raises_value_error(message=match_error, fn=lambda: sync_client.set_credentials(SyncCredentials.none()))
    assert_raises_value_error(message=match_error,
                              fn=lambda: sync_client.set_credentials(SyncCredentials.google_auth("token_google")))
    assert_raises_value_error(message=match_error, fn=lambda: sync_client.set_credentials([
        SyncCredentials.google_auth("token_google"),
        SyncCredentials.user_and_password("user1", "password")
    ]))
    assert_raises_value_error(message=match_error,
                              fn=lambda: sync_client.set_request_updates_mode(SyncRequestUpdatesMode.AUTO))
