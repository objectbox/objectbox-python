from common import *
from objectbox.sync import SyncLoginListener, SyncConnectionListener, SyncErrorListener, SyncClient, SyncCredentials


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
        self.sync_error_code = None

    def on_error(self, sync_error_code: int):
        self.sync_error_code = sync_error_code


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
    listener.sync_error_code = None


@pytest.fixture
def sync_client(test_store, login_listener, connection_listener, error_listener):
    server_urls = ["ws://127.0.0.1:9999"]
    client = SyncClient(test_store, server_urls)
    client.set_credentials(SyncCredentials.none())
    client.set_login_listener(login_listener)
    client.set_connection_listener(connection_listener)
    client.set_error_listener(error_listener)
    yield client
    client.close()


@pytest.fixture(scope="session")
def sync_server():
    server_config = start_sync_server()
    yield server_config
    if server_config:
        stop_sync_server(server_config.container_id)


def pytest_addoption(parser):
    parser.addoption(
        "--runsync", action="store_true", default=False, help="run Sync tests"
    )


def pytest_configure(config):
    config.addinivalue_line("markers", "sync: run Sync tests")


def pytest_collection_modifyitems(config, items):
    if config.getoption("--runsync"):
        return
    skip_sync = pytest.mark.skip(reason="need --runsync option to run")
    for item in items:
        if "sync" in item.keywords:
            item.add_marker(skip_sync)
