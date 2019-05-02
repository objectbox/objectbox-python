import os
import shutil

import objectbox
import objectbox.version
from tests.model import TestEntity
import pytest

db_name = 'testdata'


def remove_test_db():
    if os.path.exists(db_name):
        shutil.rmtree(db_name)


# cleanup before and after each testcase
@pytest.fixture(autouse=True)
def run_around_tests():
    remove_test_db()
    yield  # run the test function
    remove_test_db()


def test_version():
    info = objectbox.version.version_info()
    assert len(info) > 10


def test_open():
    from objectbox.model import IdUid

    model = objectbox.Model()
    model.entity(TestEntity, last_property_id=IdUid(1, 1001))
    model.last_entity_id = IdUid(1, 1)

    objectbox.Builder().model(model).directory(db_name).build()
