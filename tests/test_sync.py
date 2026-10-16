import ctypes
import gc
import os
import shutil
import threading
import time
import uuid
import weakref
from typing import Callable, Optional

import pytest

from objectbox import Entity, Id, Model, Store, String, SyncClock, SyncEntity, SyncPrecedence
import objectbox.c as c
from objectbox.c import OBXPropertyFlags_SYNC_CLOCK, OBXPropertyFlags_SYNC_PRECEDENCE
from objectbox.exceptions import GeneralError, IllegalArgumentError, SchemaError
from objectbox.sync import *
from tests.common import NO_SYNC_SERVER_URL, SYNC_MODEL_JSON_FILE, create_test_store
from tests.model import SyncTestEntity, TestEntity


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
    assert sync_client.stats(SyncStats.CONNECTS) >= 1
    assert sync_client.stats(SyncStats.LOGINS) >= 1
    assert sync_client.stats(SyncStats.MESSAGES_SENT) >= 1
    assert sync_client.stats(SyncStats.MESSAGES_RECEIVED) >= 1
    assert sync_client.stats(SyncStats.MESSAGE_BYTES_SENT) > 0
    assert sync_client.stats(SyncStats.MESSAGE_BYTES_RECEIVED) > 0
    assert sync_client.stats(SyncStats.MESSAGE_SEND_FAILURES) == 0
    sync_client.stop()
    sync_client.close()

    assert login_listener.logged_in_called
    assert login_listener.login_failure_code is None
    assert connection_listener.connected_called


@pytest.mark.sync
def test_sync_listener_removed(sync_server, test_store, login_listener, connection_listener):
    sync_client = Sync.client(test_store, sync_server.url, SyncCredentials.none())
    sync_client.set_login_listener(login_listener)
    sync_client.set_connection_listener(connection_listener)
    completed_listener = CompletedListener()
    sync_client.set_completed_listener(completed_listener)
    sync_client.set_change_listener(ChangeCollector())
    # None removes the listeners
    sync_client.set_login_listener(None)
    sync_client.set_connection_listener(None)
    sync_client.set_completed_listener(None)
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
        self.entities_by_id = {}
        self.condition = threading.Condition()

    def on_change(self, sync_changes):
        with self.condition:
            for change in sync_changes:
                self.put_ids_by_entity_id.setdefault(change.entity_id, set()).update(change.puts)
                self.entities_by_id[change.entity_id] = change.entity
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
        assert change_collector.entities_by_id[SyncTestEntity._id] is SyncTestEntity
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

    client.put_filter_variable("name2", "val2")
    client.remove_filter_variable("name2")
    client.put_filter_variable("name2", "")  # Empty values are allowed
    client.remove_all_filter_variables()
    client.put_filter_variable("name1", "val1 updated")
    client.apply_filter_variables()  # Not logged in: used with the next login

    with pytest.raises(IllegalArgumentError, match="Filter variables must have a name"):
        client.put_filter_variable("", "val5")

    client.close()


@pytest.mark.sync
def test_client_closed_if_filter_variables_fail(test_store):
    with pytest.raises(IllegalArgumentError, match="Filter variables must have a name") as exc_info:
        Sync.client(test_store, NO_SYNC_SERVER_URL, SyncCredentials.none(), filter_variables={"": "value"})
    # The failed client is closed, i.e. not active for the store, even while its exception (traceback) is referenced
    Sync.client(test_store, NO_SYNC_SERVER_URL, SyncCredentials.none()).close()
    del exc_info


class LoginCounter(SyncLoginListener):
    def __init__(self):
        self.count = 0
        self.condition = threading.Condition()

    def on_logged_in(self):
        with self.condition:
            self.count += 1
            self.condition.notify_all()

    def on_login_failed(self, sync_login_code: int):
        pass

    def wait_for_count(self, count: int, timeout: float) -> bool:
        with self.condition:
            return self.condition.wait_for(lambda: self.count >= count, timeout=timeout)


@pytest.mark.sync
def test_filter_variables_apply_after_login(sync_server, test_store):
    client = Sync.client(test_store, sync_server.url, SyncCredentials.none(), filter_variables={"team": "blue"})
    login_counter = LoginCounter()
    client.set_login_listener(login_counter)
    client.start()
    assert login_counter.wait_for_count(1, timeout=5)

    # After login, changes are pending until applied
    client.put_filter_variable("team", "green")
    assert not login_counter.wait_for_count(2, timeout=0.5)

    # Applying sends the variables to the server: the client reconnects and logs in again
    client.apply_filter_variables()
    assert login_counter.wait_for_count(2, timeout=5)
    assert client.wait_for_logged_in_state(timeout_millis=5000)
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


def test_credentials_empty_token():
    # Like in Java
    for create in (SyncCredentials.shared_secret, SyncCredentials.google_auth, SyncCredentials.jwt_id_token,
                   SyncCredentials.jwt_access_token, SyncCredentials.jwt_refresh_token,
                   SyncCredentials.jwt_custom_token):
        with pytest.raises(ValueError, match="Token must not be empty"):
            create("")
    with pytest.raises(ValueError, match="Token must not be empty"):
        SyncCredentials.shared_secret(b"")


@pytest.mark.sync
def test_credentials_wiped_after_use(sync_client):
    secret = bytearray(b"secret")
    single = SyncCredentials.shared_secret(secret)
    multiple = [SyncCredentials.jwt_id_token("token"), SyncCredentials.user_and_password("user", "password"),
                SyncCredentials.shared_secret("secret")]
    sync_client.set_credentials(single)
    sync_client.set_credentials(multiple)
    for creds in [single, multiple[0], multiple[2]]:
        assert creds.cleared
        assert creds.secret == bytes(len(creds.secret))  # Zeros
    assert secret == b"secret"  # The caller's bytearray is copied, not wiped

    # Used credentials can not be used again (checked before any are passed on)
    unused = SyncCredentials.jwt_id_token("token")
    with pytest.raises(ValueError, match="Credentials already have been used"):
        sync_client.set_credentials(single)
    with pytest.raises(ValueError, match="Credentials already have been used"):
        sync_client.set_credentials([unused, multiple[0]])
    assert not unused.cleared


@pytest.mark.sync
def test_client_closed_when_store_closed(test_store, sync_client):
    assert not sync_client.is_closed()
    test_store.close()
    assert sync_client.is_closed()


@pytest.mark.sync
def test_sync_change_entity(test_store):
    client = SyncClient(test_store, [NO_SYNC_SERVER_URL])
    changes_received = []
    listener = SyncChangeListener()
    listener.on_change = changes_received.extend
    client.set_change_listener(listener)
    # Call the C callback directly with a C change array (would require a server sending changes)
    ids = (c.obx_id * 2)(1, 2)
    puts = c.OBX_id_array(ids, 2)
    changes = (c.OBX_sync_change * 2)(c.OBX_sync_change(TestEntity._id, ctypes.pointer(puts), None),
                                      c.OBX_sync_change(12345, None, None))  # An entity ID not in the model
    change_array = c.OBX_sync_change_array(changes, 2)
    client._SyncClient__c_callbacks[0](None, ctypes.pointer(change_array))
    assert [(change.entity_id, change.entity, change.puts, change.removals) for change in changes_received] == [
        (TestEntity._id, TestEntity, [1, 2], []), (12345, None, [], [])]
    client.close()


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
def test_client_flags(test_store):
    flags = (SyncFlags.DEBUG_LOG_ID_MAPPING | SyncFlags.KEEP_DATA_ON_SYNC_ERROR | SyncFlags.DEBUG_LOG_FILTER_VARIABLES |
             SyncFlags.REMOVE_WITH_OBJECT_DATA | SyncFlags.DEBUG_LOG_TX_LOGS | SyncFlags.SKIP_INVALID_TX_OPS)
    assert flags == 63
    client = Sync.client(test_store, NO_SYNC_SERVER_URL, SyncCredentials.none(), flags=flags)
    assert client.state() == SyncState.CREATED
    client.close()


@pytest.mark.sync
def test_client_certificate_paths(test_store):
    # Like Dart: paths are only checked when connecting
    Sync.client(test_store, NO_SYNC_SERVER_URL, SyncCredentials.none(),
                certificate_paths=["/path/to/does-not-exist-1.crt", "/path/to/does-not-exist-2.crt"]).close()
    Sync.client(test_store, "wss://127.0.0.1:1", SyncCredentials.none(),
                certificate_paths=["/path/to/does-not-exist.crt"]).close()
    Sync.client(test_store, NO_SYNC_SERVER_URL, SyncCredentials.none(), certificate_paths=[]).close()


class AllEventsListener(SyncListener):
    def __init__(self):
        self.events = []
        self.completed = threading.Event()

    def on_logged_in(self):
        self.events.append("logged_in")

    def on_connected(self):
        self.events.append("connected")

    def on_updates_completed(self):
        self.events.append("completed")
        self.completed.set()

    def on_server_time_update(self, server_time_nanos: int):
        self.events.append("time")


@pytest.mark.sync
def test_sync_listener_all_events(sync_server, test_store):
    client = Sync.client(test_store, sync_server.url, SyncCredentials.none())
    listener = AllEventsListener()
    client.set_listener(listener)
    client.start()
    assert client.wait_for_logged_in_state(timeout_millis=5000)
    assert listener.completed.wait(timeout=5)
    assert {"connected", "logged_in", "completed", "time"} <= set(listener.events)
    client.close()

    # None removes all listeners
    client = Sync.client(test_store, sync_server.url, SyncCredentials.none())
    listener = AllEventsListener()
    client.set_listener(listener)
    client.set_listener(None)
    client.start()
    assert client.wait_for_logged_in_state(timeout_millis=5000)
    assert not listener.completed.wait(timeout=0.5)
    assert listener.events == []
    client.close()


@pytest.mark.sync
def test_server_time_unknown_without_server(sync_client):
    assert sync_client.server_time_nanos() == 0
    assert sync_client.server_time_diff_nanos() == 0


class TimeCollector(SyncTimeListener):
    def __init__(self):
        self.server_times_nanos = []
        self.received = threading.Event()

    def on_server_time_update(self, server_time_nanos: int):
        self.server_times_nanos.append(server_time_nanos)
        self.received.set()


@pytest.mark.sync
def test_server_time(sync_server, test_store):
    client = Sync.client(test_store, sync_server.url, SyncCredentials.none())
    time_collector = TimeCollector()
    client.set_time_listener(time_collector)
    client.start()
    assert client.wait_for_logged_in_state(timeout_millis=5000)
    assert time_collector.received.wait(timeout=5)
    now_nanos = time.time_ns()
    max_diff_nanos = 60 * 10 ** 9  # The server may run elsewhere; a minute is plenty for clock differences
    assert abs(time_collector.server_times_nanos[0] - now_nanos) < max_diff_nanos
    assert abs(client.server_time_nanos() - now_nanos) < max_diff_nanos
    assert abs(client.server_time_diff_nanos()) < max_diff_nanos
    client.set_time_listener(None)
    client.close()


@pytest.mark.sync
def test_stats_without_server(sync_client):
    for counter in SyncStats:
        assert sync_client.stats(counter) == 0
    with pytest.raises(ValueError):
        sync_client.stats(42)  # Not a SyncStats value


@pytest.mark.sync
def test_max_messages_in_flight(sync_client):
    sync_client.set_max_messages_in_flight(1)
    sync_client.set_max_messages_in_flight(20)
    for value in (0, 21):
        with pytest.raises(IllegalArgumentError, match="Value must be between 1 and 20"):
            sync_client.set_max_messages_in_flight(value)


@pytest.mark.sync
def test_client_unsupported_url(test_store):
    # Fails when adding the URL to the options (are freed) and when creating the client (frees the options)
    with pytest.raises(IllegalArgumentError, match="All URLs must have the same scheme"):
        Sync.client(test_store, [NO_SYNC_SERVER_URL, "http://127.0.0.1:9999"], SyncCredentials.none())
    with pytest.raises(GeneralError, match="Client transport not found"):
        Sync.client(test_store, "http://127.0.0.1:9999", SyncCredentials.none())
    assert test_store.sync_client() is None
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
def test_client_kept_alive_by_store(test_store):
    assert test_store.sync_client() is None

    def start_client():
        Sync.client(test_store, NO_SYNC_SERVER_URL, SyncCredentials.none()).start()  # No reference kept

    start_client()
    gc.collect()
    client = test_store.sync_client()  # Like Java and Dart, the store keeps its client alive
    assert client is not None and not client.is_closed()
    assert client.state() in (SyncState.STARTED, SyncState.DISCONNECTED)  # Started (no server to connect to)

    client.close()
    assert test_store.sync_client() is None
    assert len(test_store._close_listeners) == 0

    client = Sync.client(test_store, NO_SYNC_SERVER_URL, SyncCredentials.none())
    assert test_store.sync_client() is client
    test_store.close()
    assert client.is_closed()
    assert test_store.sync_client() is None


@pytest.mark.sync
def test_client_and_store_closed_when_dropped():
    """A store and its client that are both no longer referenced (a reference cycle) are closed by the cyclic GC."""
    store = create_test_store()
    client = Sync.client(store, NO_SYNC_SERVER_URL, SyncCredentials.none())
    client.start()
    store_ref = weakref.ref(store)
    client_ref = weakref.ref(client)
    del store, client
    gc.collect()
    assert store_ref() is None and client_ref() is None
    store = create_test_store(clear_db=False)  # Raises if the previous store at the same path is still open
    store.close()


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


def open_clock_test_store(entity, directory: str) -> Store:
    model = Model()
    model.entity(entity)
    Store.remove_db_files(directory)
    os.makedirs(directory, exist_ok=True)
    model_json_file = os.path.join(directory, "objectbox-model.json")
    if os.path.exists(model_json_file):
        os.remove(model_json_file)
    return Store(model=model, directory=directory, model_json_file=model_json_file)


@pytest.mark.sync
def test_sync_clock_and_precedence():
    @SyncEntity()
    @Entity(model="sync-clock-test")
    class ClockEntity:
        id = Id
        text = String
        clock = SyncClock
        precedence = SyncPrecedence

    assert ClockEntity.clock._flags == OBXPropertyFlags_SYNC_CLOCK
    assert ClockEntity.precedence._flags == OBXPropertyFlags_SYNC_PRECEDENCE

    store = open_clock_test_store(ClockEntity, "testdata-sync-clock")
    try:
        Sync.client(store, NO_SYNC_SERVER_URL, SyncCredentials.none()).start()  # Sync entities need an active client
        box = store.box(ClockEntity)
        obj = ClockEntity(text="a")
        box.put(obj)
        clock1 = box.get(obj.id).clock
        assert clock1 > 0  # Set by ObjectBox Sync on put
        now_millis = int(time.time() * 1000)
        assert abs(Sync.sync_clock_timestamp(clock1) - now_millis) < 60_000
        assert abs(Sync.sync_clock_timestamp_corrected(clock1) - now_millis) < 60_000
        obj.precedence = 5
        box.put(obj)
        read = box.get(obj.id)
        assert read.clock > clock1
        assert read.precedence == 5
    finally:
        store.close()


@pytest.mark.sync
def test_sync_clock_validated():
    @Entity(model="sync-clock-test-local")
    class LocalClockEntity:
        id = Id
        clock = SyncClock

    with pytest.raises(SchemaError, match="Sync clock is only supported for sync-enabled entities"):
        open_clock_test_store(LocalClockEntity, "testdata-sync-clock").close()

    @SyncEntity()
    @Entity(model="sync-clock-test-two")
    class TwoClocksEntity:
        id = Id
        clock = SyncClock
        clock2 = SyncClock

    with pytest.raises(SchemaError, match="more than one sync clock property"):
        open_clock_test_store(TwoClocksEntity, "testdata-sync-clock").close()
