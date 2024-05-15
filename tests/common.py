import objectbox
import os
from os import path
import shutil
import pytest
import numpy as np
from typing import *
from tests.model import *

test_dir = 'testdata'

def create_default_model() -> objectbox.Model:
    model = objectbox.Model()
    model.entity(TestEntity, last_property_id=IdUid(27, 1027))
    model.last_entity_id = IdUid(2, 2)
    model.last_index_id = IdUid(2, 10002)
    return model

def load_empty_test_default_store(db_name: str = test_dir) -> objectbox.Store:
    model = create_default_model()
    return objectbox.Store(model=model, directory=db_name)

def load_empty_test_datetime_store(name: str = "") -> objectbox.Store:
    model = objectbox.Model()
    model.entity(TestEntityDatetime, last_property_id=IdUid(4, 2004))
    model.last_entity_id = IdUid(2, 2)

    db_name = test_dir if len(name) == 0 else test_dir + "/" + name

    return objectbox.Store(model=model, directory=db_name)


def load_empty_test_flex_store(name: str = "") -> objectbox.Store:
    model = objectbox.Model()
    model.entity(TestEntityFlex, last_property_id=IdUid(2, 3002))
    model.last_entity_id = IdUid(3, 3)

    db_name = test_dir if len(name) == 0 else test_dir + "/" + name

    return objectbox.Store(model=model, directory=db_name)


def create_test_store(db_name: Optional[str] = None, clear_db: bool = True) -> objectbox.Store:
    """ Creates a Store instance with all entities. """

    db_path = test_dir if db_name is None else path.join(test_dir, db_name)
    print(f"DB path: \"{db_path}\"")

    if clear_db and path.exists(db_path):
        shutil.rmtree(db_path)

    model = objectbox.Model()
    model.entity(TestEntity, last_property_id=IdUid(27, 1027))
    model.entity(TestEntityDatetime, last_property_id=IdUid(4, 2004))
    model.entity(TestEntityFlex, last_property_id=IdUid(2, 3002))
    model.entity(VectorEntity, last_property_id=IdUid(5, 4005))
    model.last_entity_id = IdUid(4, 4)
    model.last_index_id = IdUid(5, 40003)

    return objectbox.Store(model=model, directory=db_path)


def assert_equal_prop(actual, expected, default):
    assert actual == expected or (isinstance(
        expected, objectbox.model.Property) and actual == default)


def assert_equal_prop_vector(actual, expected, default):
    assert (actual == np.array(expected)).all() or (isinstance(
        expected, objectbox.model.Property) and actual == default)


# compare approx values
def assert_equal_prop_approx(actual, expected, default):
    assert pytest.approx(actual) == expected or (isinstance(
        expected, objectbox.model.Property) and actual == default)


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
    assert_equal_prop_approx(actual.date, expected.date, 0)
    assert_equal_prop(actual.date_nano, expected.date_nano, 0)
    assert_equal_prop(actual.flex, expected.flex, None)
