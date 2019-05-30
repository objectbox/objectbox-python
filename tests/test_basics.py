import pytest
import objectbox
from tests.model import TestEntity
from tests.common import load_empty_test_objectbox, assert_equal


def test_version():
    info = objectbox.version_info()
    assert len(info) > 10


def test_open():
    load_empty_test_objectbox()


def test_box_basics():
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

    # read
    read = box.get(object.id)
    assert_equal(read, object)
    assert read.transient != object.transient  # !=

    # update
    object.str = "bar"
    id = box.put(object)
    assert id == 5

    # read again
    read = box.get(object.id)
    assert_equal(read, object)

    # remove
    box.remove(object)
    box.remove(1)

    # check they're gone
    assert box.count() == 0
    with pytest.raises(objectbox.NotFoundException):
        box.get(object.id)
    with pytest.raises(objectbox.NotFoundException):
        box.get(1)


def test_box_bulk():
    ob = load_empty_test_objectbox()
    box = objectbox.Box(ob, TestEntity)

    box.put(TestEntity("first"))

    objects = [TestEntity("second"), TestEntity("third"), TestEntity("fourth"), box.get(1)]
    box.put(objects)
    assert box.count() == 4
    assert objects[0].id == 2
    assert objects[1].id == 3
    assert objects[2].id == 4
    assert objects[3].id == 1

    assert_equal(box.get(objects[0].id), objects[0])
    assert_equal(box.get(objects[1].id), objects[1])
    assert_equal(box.get(objects[2].id), objects[2])
    assert_equal(box.get(objects[3].id), objects[3])

    objects_read = box.get_all()
    assert len(objects_read) == 4
    assert_equal(objects_read[0], objects[3])
    assert_equal(objects_read[1], objects[0])
    assert_equal(objects_read[2], objects[1])
    assert_equal(objects_read[3], objects[2])

    # remove all
    removed = box.remove_all()
    assert removed == 4
    assert box.count() == 0
