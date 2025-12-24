import pytest
from objectbox.logger import logger
from objectbox.sync import SyncLoginListener, SyncConnectionListener, SyncErrorListener
from common import *


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