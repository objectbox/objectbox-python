import objectbox
from objectbox.model import *
from objectbox.c import *
import pytest
from tests.common import (load_empty_test_objectbox, create_test_objectbox, autocleanup)
from tests.model import TestEntity


def test_basics():
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

    qb = box.query()
    qb.equals_string(str_prop._id, "bar", True)
    query = qb.build()
    assert query.count() == 1
    assert query.find()[0].str == "bar"

    qb = box.query()
    qb.not_equals_string(str_prop._id, "bar", True)
    query = qb.build()
    assert query.count() == 1
    assert query.find()[0].str == "foo"

    qb = box.query()
    qb.contains_string(str_prop._id, "ba", True)
    query = qb.build()
    assert query.count() == 1
    assert query.find()[0].str == "bar"

    qb = box.query()
    qb.starts_with_string(str_prop._id, "f", True)
    query = qb.build()
    assert query.count() == 1
    assert query.find()[0].str == "foo"

    qb = box.query()
    qb.ends_with_string(str_prop._id, "o", True)
    query = qb.build()
    assert query.count() == 1
    assert query.find()[0].str == "foo"

    qb = box.query()
    qb.greater_than_string(str_prop._id, "bar", True)
    query = qb.build()
    assert query.count() == 1
    assert query.find()[0].str == "foo"

    qb = box.query()
    qb.greater_or_equal_string(str_prop._id, "bar", True)
    query = qb.build()
    assert query.count() == 2
    assert query.find()[0].str == "foo"
    assert query.find()[1].str == "bar"

    qb = box.query()
    qb.less_than_string(str_prop._id, "foo", True)
    query = qb.build()
    assert query.count() == 1
    assert query.find()[0].str == "bar"

    qb = box.query()
    qb.less_or_equal_string(str_prop._id, "foo", True)
    query = qb.build()
    assert query.count() == 2
    assert query.find()[0].str == "foo"
    assert query.find()[1].str == "bar"

    # Int queries
    int_prop: Property = TestEntity.get_property("int64")

    qb = box.query()
    qb.equals_int(int_prop._id, 123)
    query = qb.build()
    assert query.count() == 1
    assert query.find()[0].int64 == 123

    qb = box.query()
    qb.not_equals_int(int_prop._id, 123)
    query = qb.build()
    assert query.count() == 1
    assert query.find()[0].int64 == 456

    qb = box.query()
    qb.greater_than_int(int_prop._id, 123)
    query = qb.build()
    assert query.count() == 1
    assert query.find()[0].int64 == 456

    qb = box.query()
    qb.greater_or_equal_int(int_prop._id, 123)
    query = qb.build()
    assert query.count() == 2
    assert query.find()[0].int64 == 123
    assert query.find()[1].int64 == 456

    qb = box.query()
    qb.less_than_int(int_prop._id, 456)
    query = qb.build()
    assert query.count() == 1
    assert query.find()[0].int64 == 123

    qb = box.query()
    qb.less_or_equal_int(int_prop._id, 456)
    query = qb.build()
    assert query.count() == 2
    assert query.find()[0].int64 == 123
    assert query.find()[1].int64 == 456

    qb = box.query()
    qb.between_2ints(int_prop._id, 100, 200)
    query = qb.build()
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

    qb = box.query()
    qb.equals_int(int_prop._id, 0)
    query = qb.build()
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


def test_any_all():
    db = create_test_objectbox()

    box = objectbox.Box(db, TestEntity)

    box.put(TestEntity(str="Foo", int32=10, int8=2, float32=3.14, bool=True))
    box.put(TestEntity(str="FooBar", int32=100, int8=50, float32=2.0, bool=True))
    box.put(TestEntity(str="Bar", int32=99, int8=127, float32=1.0, bool=False))
    box.put(TestEntity(str="Test", int32=1, int8=1, float32=0.0001, bool=True))
    box.put(TestEntity(str="test", int32=3232, int8=88, float32=1.0101, bool=False))
    box.put(TestEntity(str="Foo or BAR?", int32=0, int8=0, float32=0.0, bool=False))
    box.put(TestEntity(str="Just a test", int32=6, int8=6, float32=6.111, bool=False))
    box.put(TestEntity(str="EXAMPLE", int32=37, int8=37, float32=100, bool=True))

    # Test all
    qb = box.query()
    qb.all([
        qb.starts_with_string("str", "Foo"),
        qb.equals_int("int32", 10)
    ])
    query = qb.build()
    ids = query.find_ids()
    assert ids == [1]

    # Test any
    qb = box.query()
    qb.any([
        qb.starts_with_string("str", "Test", case_sensitive=False),
        qb.ends_with_string("str", "?"),
        qb.equals_int("int32", 37)
    ])
    query = qb.build()
    ids = query.find_ids()
    # 4, 5, 6, 8
    assert ids == [4, 5, 6, 8]

    # Test all/any
    qb = box.query()
    qb.any([
        qb.all([qb.contains_string("str", "Foo"), qb.less_than_int("int32", 100)]),
        qb.equals_string("str", "Test", case_sensitive=False)
    ])
    query = qb.build()
    ids = query.find_ids()
    # 1, 4, 5, 6
    assert ids == [1, 4, 5, 6]

    # Test all/any
    qb = box.query()
    qb.all([
        qb.any([
            qb.contains_string("str", "foo", case_sensitive=False),
            qb.contains_string("str", "bar", case_sensitive=False)
        ]),
        qb.greater_than_int("int8", 30)
    ])
    query = qb.build()
    ids = query.find_ids()
    # 2, 3
    assert ids == [2, 3]


