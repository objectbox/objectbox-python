import os
import shutil
import pytest
import objectbox
import objectbox.version
from tests.model import TestEntity


def test_version():
    info = objectbox.version.version_info()
    assert len(info) > 10


def load_empty_test_objectbox() -> objectbox.ObjectBox:
    db_name = 'testdata'

    if os.path.exists(db_name):
        shutil.rmtree(db_name)

    model = objectbox.Model()
    from objectbox.model import IdUid
    model.entity(TestEntity, last_property_id=IdUid(6, 1006))
    model.last_entity_id = IdUid(1, 1)

    return objectbox.Builder().model(model).directory(db_name).build()


def test_open():
    load_empty_test_objectbox()


def test_box():
    ob = load_empty_test_objectbox()
    box = objectbox.Box(ob, TestEntity)

    assert box.is_empty()
    assert box.count() == 0

    # create
    object = TestEntity()
    id = box.put(object)
    assert id == 1
    assert id == object.id

    # create with a given ID and some data
    object = TestEntity()
    object.id = 5
    object.bool = True
    object.int = 42
    object.str = "foo"
    object.float = 4.2
    object.bytes = bytes([1, 1, 2, 3, 5])
    object.transient = "abcd"

    id = box.put(object)
    assert id == 5
    assert id == object.id

    # check the count
    assert not box.is_empty()
    assert box.count() == 2

    def verifyObject(read, object):
        assert read.id == object.id
        assert read.bool == object.bool
        assert read.int == object.int
        assert read.str == object.str
        assert read.float == object.float
        assert read.bytes == object.bytes
        assert read.transient != object.transient  # !=

    # read
    read = box.get(object.id)
    verifyObject(read, object)

    # update
    object.str = "bar"
    id = box.put(object)
    assert id == 5

    # read again
    read = box.get(object.id)
    verifyObject(read, object)

    # remove
    box.remove(object.id)

    # check it's missing
    assert box.count() == 1
    with pytest.raises(objectbox.NotFoundException):
        box.get(object.id)


