from time import sleep
from objectbox.sync import *

def test_sync_protocol_version():
    version = SyncClient.protocol_version()
    assert version >= 1

def test_sync_client_states(test_store):
    server_urls = ["ws://localhost:9999"]
    credentials = [SyncCredentials.none()]
    client = SyncClient(test_store, server_urls, credentials)
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
