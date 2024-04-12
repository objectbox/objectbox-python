import pytest
import objectbox
from tests.model import TestEntity, TestEntityDatetime, TestEntityFlex
from tests.common import (
    autocleanup,
    load_empty_test_objectbox,
    load_empty_test_datetime,
    load_empty_test_flex,
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
    object.bools = np.array([True, False, True, True, False], dtype=np.bool_)
    object.ints = np.array([1, 2, 3, 555, 120, 222], dtype=np.int32)
    object.shorts = np.array([7, 8, 9, 12, 13, 22], dtype=np.int16)
    object.chars = np.array([311, 426, 852, 927, 1025], dtype=np.uint16)
    object.longs = np.array([4299185519, 155462547, 5019238156195], dtype=np.int64)
    object.floats = np.array([0.1, 1.2, 2.3, 3.4, 4.5], dtype=np.float32)
    object.doubles = np.array([99.99, 88.88, 77.77, 66.66, 55.595425], dtype=np.float64)
    object.bools_list = [True, False, True, True, False]
    object.ints_list = [91, 82, 73, 64, 55]
    object.shorts_list = [8, 2, 7, 3, 6]
    object.chars_list = [4, 5, 43, 75, 12]
    object.longs_list = [4568, 8714, 1234, 5678, 9012240941]
    object.floats_list = [0.11, 1.22, 2.33, 3.44, 4.5595]
    object.doubles_list = [99.1999, 88.2888, 77.3777, 66.4666, 55.6597555]
    object.date = time.time() * 1000  # milliseconds since UNIX epoch
    object.date_nano = time.time_ns()  # nanoseconds since UNIX epoch
    object.flex = dict(a=1, b=2, c=3)
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

    ob.close()


def test_box_bulk():
    ob = load_empty_test_objectbox()
    box = objectbox.Box(ob, TestEntity)

    box.put(TestEntity(str="first"))

    objects = [TestEntity(str="second"), TestEntity(str="third"),
               TestEntity(str="fourth"), box.get(1)]
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

    ob.close()


def test_datetime():
    ob = load_empty_test_datetime()
    box = objectbox.Box(ob, TestEntityDatetime)

    assert box.is_empty()
    assert box.count() == 0

    # creat - deferred for now, as there is an issue with 0 timestamp on Windows
    # object = TestEntityDatetime()
    # id = box.put(object)
    # assert id == 1
    # assert id == object.id

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
    assert box.count() == 1

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

    # check they're gone
    assert box.count() == 0
    with pytest.raises(objectbox.NotFoundException):
        box.get(object.id)
    with pytest.raises(objectbox.NotFoundException):
        box.get(1)

    ob.close()


def test_flex():
    def test_put_get(object: TestEntity, box: objectbox.Box, property):
        object.flex = property
        id = box.put(object)
        assert id == object.id
        read = box.get(object.id)
        assert read.flex == object.flex

    ob = load_empty_test_objectbox()
    box = objectbox.Box(ob, TestEntity)
    object = TestEntity()

    # Put an empty object
    id = box.put(object)
    assert id == object.id

    # Put a None type object
    test_put_get(object, box, None)

    # Update to int
    test_put_get(object, box, 1)

    # Update to float
    test_put_get(object, box, 1.2)

    # Update to string
    test_put_get(object, box, "foo")

    # Update to int list
    test_put_get(object, box, [1, 2, 3])

    # Update to float list
    test_put_get(object, box, [1.1, 2.2, 3.3])

    # Update to dict
    test_put_get(object, box, {"a": 1, "b": 2})

    # Update to bool
    test_put_get(object, box, True)

    # Update to dict inside dict
    test_put_get(object, box, {"a": 1, "b": {"c": 2}})

    # Update to list inside dict
    test_put_get(object, box, {"a": 1, "b": [1, 2, 3]})

    ob.close()


def test_flex_dict():
    ob = load_empty_test_flex()
    box = objectbox.Box(ob, TestEntityFlex)
    object = TestEntityFlex()

    # Put an empty object
    id = box.put(object)
    assert id == object.id
    read = box.get(object.id)
    assert read.flex_dict == None
    assert read.flex_int == None

    object.flex_dict = {"a": 1, "b": 2}
    object.flex_int = 25
    id = box.put(object)
    assert id == object.id
    read = box.get(object.id)
    assert read.flex_dict == object.flex_dict
    assert read.flex_int == object.flex_int
