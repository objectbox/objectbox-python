import pytest
import objectbox
from tests.model import TestEntity, TestEntityDatetime, TestEntityFlex
from tests.common import *
import numpy as np
from datetime import datetime, timezone
import time
from math import floor


def test_box_basics():
    store = load_empty_test_default_store()
    box = store.box(TestEntity)

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
    object.date = time.time()  # seconds since UNIX epoch (float)
    object.date_nano = time.time_ns()  # nanoseconds since UNIX epoch (int)
    object.flex = dict(a=1, b=2, c=3)
    object.transient = "abcd"

    id = box.put(object)
    assert id == 5
    assert id == object.id
    # check the count
    assert not box.is_empty()
    assert box.count() == 2

    # read
    # wrap date so it can be compared (is read as datetime)
    object.date = datetime.fromtimestamp(round(object.date * 1000) / 1000, tz=timezone.utc)
    read = box.get(object.id)
    assert_equal(read, object)
    assert read.transient != object.transient  # !=

    # update
    object.str = "bar"
    object.date = floor(time.time_ns() / 1000000)  # check that date can also be an int
    object.date_nano = time.time()  # check that date_nano can also be a float
    id = box.put(object)
    assert id == 5

    # read again
    read = box.get(object.id)
    assert (floor(read.date.timestamp() * 1000) == object.date)
    assert (read.date_nano == floor(object.date_nano * 1000000000))

    # remove
    box.remove(object)

    # remove should return success  
    success = box.remove(1)
    assert success == True
    success = box.remove(1)
    assert success == False

    # check they're gone
    assert box.count() == 0
    assert box.get(object.id) == None
    assert box.get(1) == None

    store.close()


def test_box_bulk():
    store = load_empty_test_default_store()
    box = store.box(TestEntity)

    box.put(TestEntity(str="first"))

    objects = [TestEntity(str="second"), TestEntity(str="third"),
               TestEntity(str="fourth"), box.get(1)]
    box.put(objects)
    assert box.count() == 4
    assert objects[0].id == 2
    assert objects[1].id == 3
    assert objects[2].id == 4
    assert objects[3].id == 1

    read = box.get(objects[0].id)
    assert_equal(read, objects[0])
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

    store.close()


def test_datetime():
    store = load_empty_test_datetime_store()
    box = store.box(TestEntityDatetime)

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
    assert type(read.date) == float
    assert type(read.date_nano) == datetime
    assert pytest.approx(read.date) == object.date.timestamp()

    # update
    object.str = "bar"
    object.date = datetime.utcnow()
    object.date_nano = datetime.utcnow()
    id = box.put(object)
    assert id == 5

    # read again
    read = box.get(object.id)
    assert pytest.approx(read.date) == object.date.timestamp()

    # remove
    success = box.remove(object)
    assert success == True

    # check they're gone
    assert box.count() == 0
    assert box.get(object.id) == None
    assert box.get(1) == None

    store.close()


def test_flex():
    def test_put_get(object: TestEntity, box: objectbox.Box, property):
        object.flex = property
        id = box.put(object)
        assert id == object.id
        read = box.get(object.id)
        assert read.flex == object.flex

    store = load_empty_test_default_store()
    box = store.box(TestEntity)
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

    store.close()


def test_flex_values():
    store = create_test_store()

    box = store.box(TestEntityFlex)

    # Test empty object
    obj_id = box.put(TestEntityFlex())
    read_obj = box.get(obj_id)
    assert read_obj.flex is None

    # Test int
    obj_id = box.put(TestEntityFlex(flex=23))
    read_obj = box.get(obj_id)
    assert read_obj.flex == 23

    # Test string
    obj_id = box.put(TestEntityFlex(flex="hello"))
    read_obj = box.get(obj_id)
    assert read_obj.flex == "hello"

    # Test mixed list
    obj_id = box.put(TestEntityFlex(flex=[4, 5, 1, "foo", 23, "bar"]))
    read_obj = box.get(obj_id)
    assert read_obj.flex == [4, 5, 1, "foo", 23, "bar"]

    # Test dictionary
    dict_ = {"a": 1, "b": {"list": [1, 2, 3], "int": 5}}
    obj_id = box.put(TestEntityFlex(flex=dict_))
    read_obj = box.get(obj_id)
    assert read_obj.flex == dict_
