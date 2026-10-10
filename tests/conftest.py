import os

import pytest
from objectbox import experimental
from objectbox.logger import logger
from common import *
from objectbox.sync import SyncLoginListener, SyncConnectionListener, SyncErrorListener, SyncClient, SyncCredentials, \
    Sync


def pytest_addoption(parser):
    parser.addoption("--fast-flatbuffers-builder", action="store_true",
                     help="Run all tests with the experimental fast FlatBuffers builder, verifying each marshalled "
                          "object against the reference (also: environment variable OBX_TEST_FAST_FLATBUFFERS_BUILDER=1)")
    parser.addoption("--flatbuffers-codegen", action="store_true",
                     help="Run all tests with the experimental FlatBuffers codegen, verifying each marshalled object "
                          "against the reference (also: environment variable OBX_TEST_FLATBUFFERS_CODEGEN=1)")


def pytest_configure(config):
    config.addinivalue_line("markers", "sync: Sync test, requires the Sync variant of the library (make depend-sync)")
    fast_builder = (config.getoption("--fast-flatbuffers-builder") or
                    os.environ.get("OBX_TEST_FAST_FLATBUFFERS_BUILDER") == "1")
    codegen = config.getoption("--flatbuffers-codegen") or os.environ.get("OBX_TEST_FLATBUFFERS_CODEGEN") == "1"
    if fast_builder and codegen:
        raise pytest.UsageError("Only one experimental FlatBuffers builder at a time: "
                                "--fast-flatbuffers-builder or --flatbuffers-codegen")
    if fast_builder:
        experimental.enable_fast_flatbuffers_builder(True, verify=True)
    elif codegen:
        experimental.enable_flatbuffers_codegen(True, verify=True)


def pytest_report_header(config):
    if experimental.is_fast_flatbuffers_builder_enabled():
        return "experimental fast FlatBuffers builder: enabled, verifying against the reference"
    if experimental.is_flatbuffers_codegen_enabled():
        return "experimental FlatBuffers codegen: enabled, verifying against the reference"


# Fixtures in this file are used by all files in the same directory:
# https://docs.pytest.org/en/7.1.x/reference/fixtures.html#conftest-py-sharing-fixtures-across-multiple-files


@pytest.fixture(autouse=True)
def cleanup_db():
    # Not needed: every test clears the DB on start, without deleting it on exit (not necessary)
    # Also, here we have no information regarding the DB path being used (although usually is "testdata")
    pass


@pytest.fixture
def test_store():
    store = create_test_store()
    yield store
    store.close()


class TestLoginListener(SyncLoginListener):
    def __init__(self):
        self.logged_in_called = False
        self.login_failure_code = None

    def on_logged_in(self):
        self.logged_in_called = True

    def on_login_failed(self, sync_login_code: int):
        self.login_failure_code = sync_login_code


class TestConnectionListener(SyncConnectionListener):
    def __init__(self):
        self.connected_called = False
        self.disconnected_called = False

    def on_connected(self):
        self.connected_called = True

    def on_disconnected(self):
        self.disconnected_called = True


class TestErrorListener(SyncErrorListener):
    def __init__(self):
        self.sync_error = None

    def on_error(self, sync_error):
        self.sync_error = sync_error


@pytest.fixture
def connection_listener():
    listener = TestConnectionListener()
    yield listener
    listener.connected_called = False
    listener.disconnected_called = False


@pytest.fixture
def login_listener():
    listener = TestLoginListener()
    yield listener
    listener.logged_in_called = False
    listener.login_failure_code = None


@pytest.fixture
def error_listener():
    listener = TestErrorListener()
    yield listener
    listener.sync_error = None


@pytest.fixture
def sync_client(test_store, login_listener, connection_listener, error_listener):
    client = SyncClient(test_store, [NO_SYNC_SERVER_URL])
    client.set_credentials(SyncCredentials.none())
    client.set_login_listener(login_listener)
    client.set_connection_listener(connection_listener)
    client.set_error_listener(error_listener)
    yield client
    client.close()


@pytest.fixture(scope="session")
def sync_server():
    """A Sync server using the model objectbox-model-sync.json (see start_sync_server() for how it is provided);
    skips the test if no server is available."""
    server = start_sync_server()
    if server is None:
        pytest.skip("Sync server not available (e.g. set OBX_SYNC_SERVER_URL)")
    yield server
    stop_sync_server(server)


def pytest_collection_modifyitems(config, items):
    if Sync.is_available():
        return
    skip_sync = pytest.mark.skip(reason="Sync is not available in the loaded library (see make depend-sync)")
    for item in items:
        if "sync" in item.keywords:
            item.add_marker(skip_sync)
