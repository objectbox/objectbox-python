import pytest
import objectbox
from tests.model import TestEntity, TestEntityDatetime
from tests.common import (
    autocleanup,
    load_empty_test_objectbox,
    load_empty_test_datetime,
    assert_equal,
)
import numpy as np
from datetime import datetime
import time
from math import floor


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
    object.int64 = 9223372036854775807
    object.int32 = 2147483647
    object.int16 = 32767
    object.int8 = 127
    object.str = "foo"
    object.float64 = 4.2
    object.float32 = 1.5
    object.bytes = bytes([1, 1, 2, 3, 5])
    object.ints = np.array([1, 2, 3, 555, 120, 222], dtype=np.int32)
    object.longs = np.array([9182, 8273, 7364, 6455, 55462547], dtype=np.int64)
    object.floats = np.array([0.1, 1.2, 2.3, 3.4, 4.5], dtype=np.float32)
    object.doubles = np.array([99.99, 88.88, 77.77, 66.66, 55.595425], dtype=np.float64)
    object.ints_list = [91, 82, 73, 64, 55]
    object.longs_list = [4568, 8714, 1234, 5678, 9012240941]
    object.floats_list = [0.11, 1.22, 2.33, 3.44, 4.5595]
    object.doubles_list = [99.1999, 88.2888, 77.3777, 66.4666, 55.6597555]
    object.date = time.time() * 1000  # milliseconds since UNIX epoch
    object.date_nano = time.time_ns()  # nanoseconds since UNIX epoch
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
    object.date = floor(time.time_ns() / 1000000)  # check that date can also be int
    object.date_nano = float(time.time() * 1000000000)  # check that date_nano can also be float
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

    objects = [TestEntity("second"), TestEntity("third"),
               TestEntity("fourth"), box.get(1)]
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


def test_datetime():
    ob = load_empty_test_datetime()
    box = objectbox.Box(ob, TestEntityDatetime)

    assert box.is_empty()
    assert box.count() == 0

    # create
    object = TestEntityDatetime()
    id = box.put(object)
    assert id == 1
    assert id == object.id

    # create with a given ID and some data
    object = TestEntityDatetime()
    object.id = 5
    object.date = datetime.utcnow()  # milliseconds since UNIX epoch
    object.date_nano = datetime.utcnow()  # nanoseconds since UNIX epoch

    id = box.put(object)
    assert id == 5
    assert id == object.id
    # check the count
    assert not box.is_empty()
    assert box.count() == 2

    # read
    read = box.get(object.id)
    assert pytest.approx(read.date.timestamp()) == object.date.timestamp()

    # update
    object.str = "bar"
    object.date = datetime.utcnow()
    object.date_nano = datetime.utcnow()
    id = box.put(object)
    assert id == 5

    # read again
    read = box.get(object.id)
    assert pytest.approx(read.date.timestamp()) == object.date.timestamp()

    # remove
    box.remove(object)
    box.remove(1)

    # check they're gone
    assert box.count() == 0
    with pytest.raises(objectbox.NotFoundException):
        box.get(object.id)
    with pytest.raises(objectbox.NotFoundException):
        box.get(1)


def test_box_bulk_datetime():
    ob = load_empty_test_datetime()
    box = objectbox.Box(ob, TestEntityDatetime)

    box.put(TestEntityDatetime("first"))

    objects = [TestEntityDatetime("second"), TestEntityDatetime("third"),
               TestEntityDatetime("fourth"), box.get(1)]
    box.put(objects)
    assert box.count() == 4
    assert objects[0].id == 2
    assert objects[1].id == 3
    assert objects[2].id == 4
    assert objects[3].id == 1

    objects_read = box.get_all()
    assert len(objects_read) == 4
    for object_read in objects_read:
        assert object_read.date == datetime.fromtimestamp(0)
        assert object_read.date_nano == datetime.fromtimestamp(0)

    # remove all
    removed = box.remove_all()
    assert removed == 4
    assert box.count() == 0
