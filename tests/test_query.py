import objectbox
from objectbox.model import *
from objectbox.c import *
import pytest
from tests.common import (load_empty_test_objectbox, autocleanup)
from tests.model import TestEntity


def test_query_basics():
    ob = load_empty_test_objectbox()
    box = objectbox.Box(ob, TestEntity)
    object1 = TestEntity()
    object1.str = "foo"
    object1.int64 = 123
    object2 = TestEntity()
    object2.str = "bar"
    object2.int64 = 456
    id1 = box.put(object1)
    box.put(object2)

    # String queries
    str_prop: Property = TestEntity.get_property("str")

    query = box.query() \
        .equals_string(str_prop._id, "bar", True) \
        .build()
    assert query.count() == 1
    assert query.find()[0].str == "bar"

    query = box.query() \
        .not_equals_string(str_prop._id, "bar", True) \
        .build()
    assert query.count() == 1
    assert query.find()[0].str == "foo"

    query = box.query() \
        .contains_string(str_prop._id, "ba", True) \
        .build()
    assert query.count() == 1
    assert query.find()[0].str == "bar"

    query = box.query() \
        .starts_with_string(str_prop._id, "f", True) \
        .build()
    assert query.count() == 1
    assert query.find()[0].str == "foo"

    query = box.query() \
        .ends_with_string(str_prop._id, "o", True) \
        .build()
    assert query.count() == 1
    assert query.find()[0].str == "foo"

    query = box.query() \
        .greater_than_string(str_prop._id, "bar", True) \
        .build()
    assert query.count() == 1
    assert query.find()[0].str == "foo"

    query = box.query() \
        .greater_or_equal_string(str_prop._id, "bar", True) \
        .build()
    assert query.count() == 2
    assert query.find()[0].str == "foo"
    assert query.find()[1].str == "bar"

    query = box.query() \
        .less_than_string(str_prop._id, "foo", True) \
        .build()
    assert query.count() == 1
    assert query.find()[0].str == "bar"

    query = box.query() \
        .less_or_equal_string(str_prop._id, "foo", True) \
        .build()
    assert query.count() == 2
    assert query.find()[0].str == "foo"
    assert query.find()[1].str == "bar"

    # Int queries
    int_prop: Property = TestEntity.get_property("int64")

    query = box.query() \
        .equals_int(int_prop._id, 123) \
        .build()
    assert query.count() == 1
    assert query.find()[0].int64 == 123

    query = box.query() \
        .not_equals_int(int_prop._id, 123) \
        .build()
    assert query.count() == 1
    assert query.find()[0].int64 == 456

    query = box.query() \
        .greater_than_int(int_prop._id, 123) \
        .build()
    assert query.count() == 1
    assert query.find()[0].int64 == 456

    query = box.query() \
        .greater_or_equal_int(int_prop._id, 123) \
        .build()
    assert query.count() == 2
    assert query.find()[0].int64 == 123
    assert query.find()[1].int64 == 456

    query = box.query() \
        .less_than_int(int_prop._id, 456) \
        .build()
    assert query.count() == 1
    assert query.find()[0].int64 == 123

    query = box.query() \
        .less_or_equal_int(int_prop._id, 456) \
        .build()
    assert query.count() == 2
    assert query.find()[0].int64 == 123
    assert query.find()[1].int64 == 456

    query = box.query() \
        .between_2ints(int_prop._id, 100, 200) \
        .build()
    assert query.count() == 1
    assert query.find()[0].int64 == 123

    assert query.remove() == 1

    ob.close()


def test_offset_limit():
    ob = load_empty_test_objectbox()
    box = objectbox.Box(ob, TestEntity)
    object0 = TestEntity()
    object1 = TestEntity()
    object1.str = "a"
    object2 = TestEntity()
    object2.str = "b"
    object3 = TestEntity()
    object3.str = "c"
    box.put([object0, object1, object2, object3])

    int_prop: Property = TestEntity.get_property("int64")

    query = box.query() \
        .equals_int(int_prop._id, 0) \
        .build()
    assert query.count() == 4

    query.offset(2)
    assert len(query.find()) == 2
    assert query.find()[0].str == "b"
    assert query.find()[1].str == "c"

    query.limit(1)
    assert len(query.find()) == 1
    assert query.find()[0].str == "b"

    query.offset(0)
    query.limit(0)
    assert len(query.find()) == 4
