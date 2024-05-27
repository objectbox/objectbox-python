import os
import pytest
import objectbox
from objectbox.logger import logger
from tests.model import *
import numpy as np
from datetime import datetime, timezone
from objectbox import *

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


def assert_equal_prop(actual, expected, default):
    if isinstance(expected, objectbox.model.Property):
        assert (actual == default)
    else:
        assert (actual == expected)


def assert_equal_prop_vector(actual, expected, default):
    assert (actual == np.array(expected)).all() or (isinstance(
        expected, objectbox.model.Property) and actual == default)


# compare approx values
def assert_equal_prop_approx(actual, expected, default):
    if isinstance(expected, objectbox.model.Property):
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
