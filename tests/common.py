import os
import time
import subprocess
import socket
import typing

import pytest
import objectbox
from objectbox.logger import logger
from tests.model import *
import numpy as np
from datetime import datetime, timezone
from objectbox import *
import logging

from dataclasses import dataclass

test_logger = logging.getLogger(__name__)


def remove_json_model_file():
    path = os.path.dirname(os.path.realpath(__file__))
    json_file = os.path.join(path, "objectbox-model.json")
    if os.path.exists(json_file):
        os.remove(json_file)


def create_default_model():
    model = Model()
    model.entity(TestEntity)
    model.entity(TestEntityDatetime)
    model.entity(TestEntityFlex)
    model.entity(VectorEntity)
    return model


def create_test_store(db_path: str = "testdata", clear_db: bool = True) -> objectbox.Store:
    """ Creates a Store instance with all entities. """

    is_inmemory = db_path.startswith("memory:")
    logger.info(f"DB path: {db_path} ({'in-memory' if is_inmemory else ''})")

    if clear_db:
        Store.remove_db_files(db_path)
        remove_json_model_file()
    return objectbox.Store(model=create_default_model(), directory=db_path)


@dataclass
class SyncServerConfig:
    container_id: str
    port: int


def start_sync_server() -> typing.Union[SyncServerConfig, None]:
    """ Starts the ObjectBox Sync Server in a Docker container. """
    current_dir = os.path.dirname(os.path.realpath(__file__))
    user_id = None
    if os.name != 'nt':
        user_id = os.getuid()
    else:
        user_id = 0
    try:
        command = ("docker run "
                   "--rm "
                   "-d "
                   f"--volume {current_dir}:/data "
                   f"--user {user_id} "
                   "-p 127.0.0.1:9999:9999 "
                   "objectboxio/sync-server-trial "
                   "--conf sync_server_config.json")
        logger.info("Using command to start Sync Server Docker container:" + command)
        stdout = subprocess.run(command.split(), check=True, capture_output=True, text=True).stdout
        container_id = stdout.strip()

        start_time = time.time()
        while (time.time() - start_time) < 10:
            try:
                with socket.create_connection(("127.0.0.1", 9999)):
                    break
            except OSError:
                pass
        else:
            raise RuntimeError("Timed out waiting for Sync Server to start")

        test_logger.info("Started ObjectBox Sync Server in Docker")
        return SyncServerConfig(container_id=container_id, port=9999)
    except Exception as e:
        test_logger.warning(f"Could not start ObjectBox Sync Server in Docker: {e}")
        return None


def stop_sync_server(container_id: str):
    """ Stops the ObjectBox Sync Server Docker container. """
    try:
        command = f"docker stop {container_id}"
        subprocess.run(command.split(), check=True)
        test_logger.info("Stopped ObjectBox Sync Server Docker container")
    except Exception as e:
        test_logger.warning(f"Could not stop ObjectBox Sync Server Docker container: {e}")


def assert_equal_prop(actual, expected, default):
    if isinstance(expected, objectbox.model.properties.Property):
        assert (actual == default)
    else:
        assert (actual == expected)


def assert_equal_prop_vector(actual, expected, default):
    assert (actual == np.array(expected)).all() or (isinstance(
        expected, objectbox.model.Property) and actual == default)


# compare approx values
def assert_equal_prop_approx(actual, expected, default):
    if isinstance(expected, objectbox.model.properties.Property):
        assert (actual == default)
    else:
        assert (pytest.approx(actual) == expected)


def assert_equal(actual: TestEntity, expected: TestEntity):
    """Check that two TestEntity objects have the same property data"""
    assert actual.id == expected.id
    assert_equal_prop(actual.int64, expected.int64, 0)
    assert_equal_prop(actual.int32, expected.int32, 0)
    assert_equal_prop(actual.int16, expected.int16, 0)
    assert_equal_prop(actual.int8, expected.int8, 0)
    assert_equal_prop(actual.float64, expected.float64, 0)
    assert_equal_prop(actual.float32, expected.float32, 0)
    assert_equal_prop(actual.bytes, expected.bytes, b'')
    assert_equal_prop_vector(actual.bools, expected.bools, np.array([]))
    assert_equal_prop_vector(actual.ints, expected.ints, np.array([]))
    assert_equal_prop_vector(actual.shorts, expected.shorts, np.array([]))
    assert_equal_prop_vector(actual.chars, expected.chars, np.array([]))
    assert_equal_prop_vector(actual.longs, expected.longs, np.array([]))
    assert_equal_prop_vector(actual.floats, expected.floats, np.array([]))
    assert_equal_prop_vector(actual.doubles, expected.doubles, np.array([]))
    assert_equal_prop_approx(actual.bools_list, expected.bools_list, [])
    assert_equal_prop_approx(actual.ints_list, expected.ints_list, [])
    assert_equal_prop_approx(actual.shorts_list, expected.shorts_list, [])
    assert_equal_prop_approx(actual.chars_list, expected.chars_list, [])
    assert_equal_prop_approx(actual.longs_list, expected.longs_list, [])
    assert_equal_prop_approx(actual.floats_list, expected.floats_list, [])
    assert_equal_prop_approx(actual.doubles_list, expected.doubles_list, [])
    assert_equal_prop_approx(actual.date, expected.date, datetime.fromtimestamp(0, timezone.utc))
    assert_equal_prop(actual.date_nano, expected.date_nano, 0)
    assert_equal_prop(actual.flex, expected.flex, None)
