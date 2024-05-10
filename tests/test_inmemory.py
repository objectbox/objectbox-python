import objectbox
from tests.common import load_empty_test_default_store
from tests.model import TestEntity
import os.path
import shutil


def test_inmemory():
    # Use default path for persistent store
    db_name = "testdata"
    store = load_empty_test_default_store()
    box = store.box(TestEntity)
    object = TestEntity()
    id = box.put(object)
    assert id == 1
    assert id == object.id
    assert os.path.exists(db_name)
    del box
    store.close()
    shutil.rmtree(db_name)

    # Expect no path for in-memory store
    db_name = "memory:testdata"
    store = load_empty_test_default_store(db_name)
    box = store.box(TestEntity)
    object = TestEntity()
    id = box.put(object)
    assert id == 1
    assert id == object.id
    assert not os.path.exists(db_name)
