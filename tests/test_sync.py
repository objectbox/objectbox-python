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
