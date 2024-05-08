import objectbox
from tests.common import load_empty_test_default_store
from tests.model import TestEntity
import os.path
import shutil


def test_inmemory():
    # Expect path for persistent store
    db_name = "testdata_persistent"
    ob = load_empty_test_default_store(db_name)
    box = objectbox.Box(ob, TestEntity)
    object = TestEntity()
    id = box.put(object)
    assert id == 1
    assert id == object.id
    assert os.path.exists(db_name)
    del box
    ob.close()
    shutil.rmtree(db_name)

    # Expect no path for in-memory store
    db_name = "memory:testdata"
    ob = load_empty_test_default_store(db_name)
    box = objectbox.Box(ob, TestEntity)
    object = TestEntity()
    id = box.put(object)
    assert id == 1
    assert id == object.id
    assert not os.path.exists(db_name)
