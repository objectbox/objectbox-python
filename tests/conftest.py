import os

import pytest
from objectbox import experimental
from objectbox.logger import logger
from common import *


def pytest_addoption(parser):
    parser.addoption("--fast-flatbuffers-builder", action="store_true",
                     help="Run all tests with the experimental fast FlatBuffers builder, verifying each marshalled "
                          "object against the reference (also: environment variable OBX_TEST_FAST_FLATBUFFERS_BUILDER=1)")


def pytest_configure(config):
    if config.getoption("--fast-flatbuffers-builder") or os.environ.get("OBX_TEST_FAST_FLATBUFFERS_BUILDER") == "1":
        experimental.enable_fast_flatbuffers_builder(True, verify=True)


def pytest_report_header(config):
    if experimental.is_fast_flatbuffers_builder_enabled():
        return "experimental fast FlatBuffers builder: enabled, verifying against the reference"


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
