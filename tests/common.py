import objectbox
import os
import shutil
import pytest
from tests.model import TestEntity, TestEntityDatetime, TestEntityFlex
import numpy as np

test_dir = 'testdata'


def remove_test_dir():
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)


# cleanup before and after each testcase
@pytest.fixture(autouse=True)
def autocleanup():
    remove_test_dir()
    yield  # run the test function
    remove_test_dir()


def load_empty_test_objectbox(name: str = "") -> objectbox.ObjectBox:
    model = objectbox.Model()
    from objectbox.model import IdUid
    model.entity(TestEntity, last_property_id=IdUid(21, 1021))
    model.last_entity_id = IdUid(2, 2)

    db_name = test_dir if len(name) == 0 else test_dir + "/" + name

    return objectbox.Builder().model(model).directory(db_name).build()


def load_empty_test_datetime(name: str = "") -> objectbox.ObjectBox:
    model = objectbox.Model()
    from objectbox.model import IdUid
    model.entity(TestEntityDatetime, last_property_id=IdUid(4, 2004))
    model.last_entity_id = IdUid(2, 2)

    db_name = test_dir if len(name) == 0 else test_dir + "/" + name

    return objectbox.Builder().model(model).directory(db_name).build()


def load_empty_test_flex(name: str = "") -> objectbox.ObjectBox:
    model = objectbox.Model()
    from objectbox.model import IdUid
    model.entity(TestEntityFlex, last_property_id=IdUid(3, 3003))
    model.last_entity_id = IdUid(3, 3)

    db_name = test_dir if len(name) == 0 else test_dir + "/" + name

    return objectbox.Builder().model(model).directory(db_name).build()


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
    assert_equal_prop_vector(actual.ints, expected.ints, np.array([]))
    assert_equal_prop_vector(actual.longs, expected.longs, np.array([]))
    assert_equal_prop_vector(actual.floats, expected.floats, np.array([]))
    assert_equal_prop_vector(actual.doubles, expected.doubles, np.array([]))
    assert_equal_prop_approx(actual.ints_list, expected.ints_list, [])
    assert_equal_prop_approx(actual.longs_list, expected.longs_list, [])
    assert_equal_prop_approx(actual.floats_list, expected.floats_list, [])
    assert_equal_prop_approx(actual.doubles_list, expected.doubles_list, [])
    assert_equal_prop_approx(actual.date, expected.date, 0)
    assert_equal_prop(actual.date_nano, expected.date_nano, 0)
    assert_equal_prop(actual.flex, expected.flex, None)
