import objectbox
from objectbox import *
from objectbox.model import *
from objectbox.c import *
from objectbox.query import *
import pytest
from tests.common import *
from tests.model import *


def test_basics():
    ob = create_test_objectbox()

    box_test_entity = objectbox.Box(ob, TestEntity)
    box_test_entity.put(TestEntity(str="foo", int64=123))
    box_test_entity.put(TestEntity(str="bar", int64=456))

    box_vector_entity = objectbox.Box(ob, VectorEntity)
    box_vector_entity.put(VectorEntity(name="Object 1", vector=[1, 1]))
    box_vector_entity.put(VectorEntity(name="Object 2", vector=[2, 2]))
    box_vector_entity.put(VectorEntity(name="Object 3", vector=[3, 3]))

    # String query
    str_prop: Property = TestEntity.get_property("str")

    query = box_test_entity.query(str_prop.equals("bar", case_sensitive=True)).build()
    assert query.count() == 1
    assert query.find()[0].str == "bar"

    query = box_test_entity.query(str_prop.not_equals("bar", case_sensitive=True)).build()
    assert query.count() == 1
    assert query.find()[0].str == "foo"

    query = box_test_entity.query(str_prop.contains("ba", case_sensitive=True)).build()
    assert query.count() == 1
    assert query.find()[0].str == "bar"

    query = box_test_entity.query(str_prop.starts_with("f", case_sensitive=True)).build()
    assert query.count() == 1
    assert query.find()[0].str == "foo"

    query = box_test_entity.query(str_prop.ends_with("o", case_sensitive=True)).build()
    assert query.count() == 1
    assert query.find()[0].str == "foo"

    query = box_test_entity.query(str_prop.greater_than("bar", case_sensitive=True)).build()
    assert query.count() == 1
    assert query.find()[0].str == "foo"

    query = box_test_entity.query(str_prop.greater_or_equal("bar", case_sensitive=True)).build()
    assert query.count() == 2
    assert query.find()[0].str == "foo"
    assert query.find()[1].str == "bar"

    query = box_test_entity.query(str_prop.less_than("foo", case_sensitive=True)).build()
    assert query.count() == 1
    assert query.find()[0].str == "bar"

    query = box_test_entity.query(str_prop.less_or_equal("foo", case_sensitive=True)).build()
    assert query.count() == 2
    assert query.find()[0].str == "foo"
    assert query.find()[1].str == "bar"

    # Int queries
    int_prop: Property = TestEntity.get_property("int64")

    query = box_test_entity.query(int_prop.equals(123)).build()
    assert query.count() == 1
    assert query.find()[0].int64 == 123

    query = box_test_entity.query(int_prop.not_equals(123)).build()
    assert query.count() == 1
    assert query.find()[0].int64 == 456

    query = box_test_entity.query(int_prop.greater_than(123)).build()
    assert query.count() == 1
    assert query.find()[0].int64 == 456

    query = box_test_entity.query(int_prop.greater_or_equal(123)).build()
    assert query.count() == 2
    assert query.find()[0].int64 == 123
    assert query.find()[1].int64 == 456

    query = box_test_entity.query(int_prop.less_than(456)).build()
    assert query.count() == 1
    assert query.find()[0].int64 == 123

    query = box_test_entity.query(int_prop.less_or_equal(456)).build()
    assert query.count() == 2
    assert query.find()[0].int64 == 123
    assert query.find()[1].int64 == 456

    query = box_test_entity.query(int_prop.between(100, 200)).build()
    assert query.count() == 1
    assert query.find()[0].int64 == 123

    #
    assert query.remove() == 1

    # NN query
    vector_prop: Property = VectorEntity.get_property("vector")

    query = box_vector_entity.query(vector_prop.nearest_neighbor([2.1, 2.1], 2)).build()
    assert query.count() == 2
    assert query.find_ids() == [2, 3]

    ob.close()


def test_flex_contains_key_value():
    ob = create_test_objectbox()

    box = objectbox.Box(ob, TestEntityFlex)
    box.put(TestEntityFlex(flex={"k1": "String", "k2": 2, "k3": "string"}))
    box.put(TestEntityFlex(flex={"k1": "strinG", "k2": 3, "k3": 10, "k4": [1, "foo", 3]}))
    box.put(TestEntityFlex(flex={"k1": "buzz", "k2": 3, "k3": [2, 3], "k4": {"k1": "a", "k2": "inner text"}}))
    box.put(TestEntityFlex(flex={"n1": "string", "n2": -7, "n3": [-10, 10], "n4": [4, 4, 4]}))
    box.put(TestEntityFlex(flex={"n1": "Apple", "n2": 3, "n3": [2, 3, 5], "n4": {"n1": [1, 2, "bar"]}}))

    assert box.count() == 5

    # Search case-sensitive = False
    flex: Property = TestEntityFlex.get_property("flex")
    query = box.query(flex.contains_key_value("k1", "string", False)).build()
    results = query.find()
    assert len(results) == 2
    assert results[0].flex["k1"] == "String"
    assert results[0].flex["k2"] == 2
    assert results[0].flex["k3"] == "string"
    assert results[1].flex["k1"] == "strinG"
    assert results[1].flex["k2"] == 3
    assert results[1].flex["k3"] == 10
    assert results[1].flex["k4"] == [1, "foo", 3]

    # Search case-sensitive = True
    flex: Property = TestEntityFlex.get_property("flex")
    query = box.query(flex.contains_key_value("n1", "string", True)).build()
    results = query.find()
    assert len(results) == 1
    assert results[0].flex["n1"] == "string"
    assert results[0].flex["n2"] == -7
    assert results[0].flex["n3"] == [-10, 10]
    assert results[0].flex["n4"] == [4, 4, 4]

    # TODO Search using nested key (not supported yet)

    # No match (key)
    flex: Property = TestEntityFlex.get_property("flex")
    query = box.query(flex.contains_key_value("missing key", "string", True)).build()
    assert len(query.find()) == 0

    # No match (value)
    flex: Property = TestEntityFlex.get_property("flex")
    query = box.query(flex.contains_key_value("k1", "missing value", True)).build()
    assert len(query.find()) == 0


def test_offset_limit():
    ob = load_empty_test_objectbox()

    box = objectbox.Box(ob, TestEntity)
    box.put(TestEntity())
    box.put(TestEntity(str="a"))
    box.put(TestEntity(str="b"))
    box.put(TestEntity(str="c"))
    assert box.count() == 4

    int_prop = TestEntity.get_property("int64")

    query = box.query(int_prop.equals(0)).build()
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


def test_set_parameter():
    db = create_test_objectbox()

    box_test_entity = objectbox.Box(db, TestEntity)
    box_test_entity.put(TestEntity(str="Foo", int64=2, int32=703, int8=101))
    box_test_entity.put(TestEntity(str="FooBar", int64=10, int32=49, int8=45))
    box_test_entity.put(TestEntity(str="Bar", int64=10, int32=226, int8=126))
    box_test_entity.put(TestEntity(str="Foster", int64=2, int32=301, int8=42))
    box_test_entity.put(TestEntity(str="Fox", int64=10, int32=157, int8=11))
    box_test_entity.put(TestEntity(str="Barrakuda", int64=4, int32=386, int8=60))

    box_vector_entity = objectbox.Box(db, VectorEntity)
    box_vector_entity.put(VectorEntity(name="Object 1", vector=[1, 1]))
    box_vector_entity.put(VectorEntity(name="Object 2", vector=[2, 2]))
    box_vector_entity.put(VectorEntity(name="Object 3", vector=[3, 3]))
    box_vector_entity.put(VectorEntity(name="Object 4", vector=[4, 4]))
    box_vector_entity.put(VectorEntity(name="Object 5", vector=[5, 5]))

    qb = box_test_entity.query()
    qb.starts_with_string("str", "fo", case_sensitive=False)
    qb.greater_than_int("int32", 150)
    qb.greater_than_int("int64", 0)
    query = qb.build()
    assert query.find_ids() == [1, 4, 5]

    # Test set_parameter_string
    query.set_parameter_string("str", "bar")
    assert query.find_ids() == [3, 6]

    # Test set_parameter_int
    query.set_parameter_int("int64", 8)
    assert query.find_ids() == [3]

    qb = box_vector_entity.query()
    qb.nearest_neighbors_f32("vector", [3.4, 3.4], 3)
    query = qb.build()
    assert query.find_ids() == sorted([3, 4, 2])

    # set_parameter_vector_f32
    # set_parameter_int (NN count)
    query.set_parameter_vector_f32("vector", [4.9, 4.9])
    assert query.find_ids() == sorted([5, 4, 3])

    query.set_parameter_vector_f32("vector", [0, 0])
    assert query.find_ids() == sorted([1, 2, 3])

    query.set_parameter_vector_f32("vector", [2.5, 2.1])
    assert query.find_ids() == sorted([2, 3, 1])

    query.set_parameter_int("vector", 2)
    assert query.find_ids() == sorted([2, 3])


def test_set_parameter_alias():
    db = create_test_objectbox()
    box = objectbox.Box(db, TestEntity)

    box.put(TestEntity(str="Foo", int64=2, int32=703, int8=101))
    box.put(TestEntity(str="FooBar", int64=10, int32=49, int8=45))

    box_vector = objectbox.Box(db, VectorEntity)
    box_vector.put(VectorEntity(name="Object 1", vector=[1, 1]))
    box_vector.put(VectorEntity(name="Object 2", vector=[2, 2]))
    box_vector.put(VectorEntity(name="Object 3", vector=[3, 3]))
    box_vector.put(VectorEntity(name="Object 4", vector=[4, 4]))
    box_vector.put(VectorEntity(name="Object 5", vector=[5, 5]))

    str_prop: Property = TestEntity.properties[1]
    qb = box.query(str_prop.equals("Foo").alias("foo_filter"))

    query = qb.build()
    assert query.find()[0].str == "Foo"
    assert query.count() == 1

    query.set_parameter_alias_string("foo_filter", "FooBar")

    assert query.find()[0].str == "FooBar"
    assert query.count() == 1

    int_prop: Property = TestEntity.properties[3]
    qb = box.query(int_prop.greater_than(5).alias("greater_than_filter"))

    query = qb.build()
    assert query.count() == 1
    assert query.find()[0].str == "FooBar"

    query.set_parameter_alias_int("greater_than_filter", 1)

    assert query.count() == 2

    vector_prop: Property = VectorEntity.get_property("vector")

    query = box_vector.query(vector_prop.nearest_neighbor([3.4, 3.4], 3).alias("nearest_neighbour_filter")).build()
    assert query.count() == 3
    assert query.find_ids() == sorted([3, 4, 2])

    query.set_parameter_alias_vector_f32("nearest_neighbour_filter", [4.9, 4.9])
    assert query.count() == 3
    assert query.find_ids() == sorted([5, 4, 3])
