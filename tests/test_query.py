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

    str_prop: Property = TestEntity.properties[1]
    query = box.query(str_prop.equals("bar")).build()
    assert query.count() == 1
    assert query.find()[0].str == "bar"

    query = box.query(str_prop.not_equals("bar")).build()
    assert query.count() == 1
    assert query.find()[0].str == "foo"

    query = box.query(str_prop.contains("ba")).build()
    assert query.count() == 1
    assert query.find()[0].str == "bar"

    query = box.query(str_prop.starts_with("f")).build()
    assert query.count() == 1
    assert query.find()[0].str == "foo"

    query = box.query(str_prop.ends_with("o")).build()
    assert query.count() == 1
    assert query.find()[0].str == "foo"

    query = box.query(str_prop.greater_than("bar")).build()
    assert query.count() == 1
    assert query.find()[0].str == "foo"

    query = box.query(str_prop.greater_or_equal("bar")).build()
    assert query.count() == 2
    assert query.find()[0].str == "foo"
    assert query.find()[1].str == "bar"

    query = box.query(str_prop.less_than("foo")).build()
    assert query.count() == 1
    assert query.find()[0].str == "bar"

    query = box.query(str_prop.less_or_equal("foo")).build()
    assert query.count() == 2
    assert query.find()[0].str == "foo"
    assert query.find()[1].str == "bar"


    # Int queries

    int_prop: Property = TestEntity.properties[3]
    query = box.query(int_prop.equals(123)).build()
    assert query.count() == 1
    assert query.find()[0].int64 == 123

    query = box.query(int_prop.not_equals(123)).build()
    assert query.count() == 1
    assert query.find()[0].int64 == 456

    query = box.query(int_prop.greater_than(123)).build()
    assert query.count() == 1
    assert query.find()[0].int64 == 456

    query = box.query(int_prop.greater_or_equal(123)).build()
    assert query.count() == 2
    assert query.find()[0].int64 == 123
    assert query.find()[1].int64 == 456

    query = box.query(int_prop.less_than(456)).build()
    assert query.count() == 1
    assert query.find()[0].int64 == 123

    query = box.query(int_prop.less_or_equal(456)).build()
    assert query.count() == 2
    assert query.find()[0].int64 == 123
    assert query.find()[1].int64 == 456

    query = box.query(int_prop.between(100, 200)).build()
    assert query.count() == 1
    assert query.find()[0].int64 == 123

    with pytest.raises(CoreException):
        box.query(int_prop.equals("foo")).build()

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

    query = box.query(TestEntity.properties[3].equals(0)).build()
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
