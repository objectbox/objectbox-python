import objectbox
import os
import shutil
import pytest
from tests.model import TestEntity

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
    model.entity(TestEntity, last_property_id=IdUid(6, 1006))
    model.last_entity_id = IdUid(1, 1)

    db_name = test_dir if len(name) == 0 else test_dir + "/" + name

    return objectbox.Builder().model(model).directory(db_name).build()


def assert_equal(actual, expected):
    """Check that two TestEntity objects have the same property data"""
    assert actual.id == expected.id
    assert isinstance(expected.bool, objectbox.model.Property) or actual.bool == expected.bool
    assert isinstance(expected.int, objectbox.model.Property) or actual.int == expected.int
    assert isinstance(expected.str, objectbox.model.Property) or actual.str == expected.str
    assert isinstance(expected.float, objectbox.model.Property) or actual.float == expected.float
    assert isinstance(expected.bytes, objectbox.model.Property) or actual.bytes == expected.bytes

