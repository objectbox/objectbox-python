import objectbox
from objectbox import *
from objectbox.c import *
from objectbox.query import *
from objectbox.exceptions import IllegalArgumentError, NonUniqueResultError
import pytest
from datetime import datetime, timezone
from tests.common import *
from tests.model import *


def test_basics(test_store):
    box_test_entity = test_store.box(TestEntity)
    id1 = box_test_entity.put(TestEntity(bool=True, str="foo", int64=123))
    id2 = box_test_entity.put(TestEntity(bool=False, str="bar", int64=456))

    box_vector_entity = test_store.box(VectorEntity)
    box_vector_entity.put(VectorEntity(name="Object 1", vector_euclidean=[1, 1]))
    box_vector_entity.put(VectorEntity(name="Object 2", vector_euclidean=[2, 2]))
    box_vector_entity.put(VectorEntity(name="Object 3", vector_euclidean=[3, 3]))

    # Id query
    query = box_test_entity.query(TestEntity.id.equals(id1)).build()
    assert query.count() == 1
    query = box_test_entity.query(TestEntity.id.greater_than(id1)).build()
    assert query.count() == 1
    query = box_test_entity.query(TestEntity.id.greater_or_equal(id1)).build()
    assert query.count() == 2
    query = box_test_entity.query(TestEntity.id.less_than(id2)).build()
    assert query.count() == 1
    query = box_test_entity.query(TestEntity.id.less_or_equal(id2)).build()
    assert query.count() == 2

    # Bool query
    query = box_test_entity.query(TestEntity.bool.equals(True)).build()
    assert query.count() == 1
    assert query.find()[0].id == id1

    query = box_test_entity.query(TestEntity.bool.equals(False)).build()
    assert query.count() == 1
    assert query.find()[0].id == id2

    # String query
    str_prop = TestEntity.str

    # Case Sensitive = True
    query = box_test_entity.query(str_prop.equals("bar", case_sensitive=True)).build()
    # String query using direct `<entity>.<propname>` notation

    query = box_test_entity.query(TestEntity.str.equals("bar", case_sensitive=True)).build()
    assert query.count() == 1
    assert query.find()[0].str == "bar"

    query = box_test_entity.query(TestEntity.str.not_equals("bar", case_sensitive=True)).build()
    assert query.count() == 1
    assert query.find()[0].str == "foo"

    query = box_test_entity.query(TestEntity.str.contains("ba", case_sensitive=True)).build()
    assert query.count() == 1
    assert query.find()[0].str == "bar"

    query = box_test_entity.query(TestEntity.str.starts_with("f", case_sensitive=True)).build()
    assert query.count() == 1
    assert query.find()[0].str == "foo"

    query = box_test_entity.query(TestEntity.str.ends_with("o", case_sensitive=True)).build()
    assert query.count() == 1
    assert query.find()[0].str == "foo"

    query = box_test_entity.query(TestEntity.str.greater_than("bar", case_sensitive=True)).build()
    assert query.count() == 1
    assert query.find()[0].str == "foo"

    query = box_test_entity.query(TestEntity.str.greater_or_equal("bar", case_sensitive=True)).build()
    assert query.count() == 2
    assert query.find()[0].str == "foo"
    assert query.find()[1].str == "bar"

    query = box_test_entity.query(TestEntity.str.less_than("foo", case_sensitive=True)).build()
    assert query.count() == 1
    assert query.find()[0].str == "bar"

    query = box_test_entity.query(TestEntity.str.less_or_equal("foo", case_sensitive=True)).build()
    assert query.count() == 2
    assert query.find()[0].str == "foo"
    assert query.find()[1].str == "bar"

    # Case Sensitive = False

    query = box_test_entity.query(TestEntity.str.equals("Bar", case_sensitive=False)).build()
    assert query.count() == 1
    assert query.find()[0].str == "bar"

    query = box_test_entity.query(TestEntity.str.not_equals("Bar", case_sensitive=False)).build()
    assert query.count() == 1
    assert query.find()[0].str == "foo"

    query = box_test_entity.query(TestEntity.str.contains("Ba", case_sensitive=False)).build()
    assert query.count() == 1
    assert query.find()[0].str == "bar"

    query = box_test_entity.query(TestEntity.str.starts_with("F", case_sensitive=False)).build()
    assert query.count() == 1
    assert query.find()[0].str == "foo"

    query = box_test_entity.query(TestEntity.str.ends_with("O", case_sensitive=False)).build()
    assert query.count() == 1
    assert query.find()[0].str == "foo"

    query = box_test_entity.query(TestEntity.str.greater_than("BAR", case_sensitive=False)).build()
    assert query.count() == 1
    assert query.find()[0].str == "foo"

    query = box_test_entity.query(TestEntity.str.greater_or_equal("BAR", case_sensitive=False)).build()
    assert query.count() == 2
    assert query.find()[0].str == "foo"
    assert query.find()[1].str == "bar"

    query = box_test_entity.query(TestEntity.str.less_than("FOo", case_sensitive=False)).build()
    assert query.count() == 1
    assert query.find()[0].str == "bar"

    query = box_test_entity.query(TestEntity.str.less_or_equal("FoO", case_sensitive=False)).build()
    assert query.count() == 2
    assert query.find()[0].str == "foo"
    assert query.find()[1].str == "bar"

    # Int queries using a reference to property
    int_prop = TestEntity.int64

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
    query = box_vector_entity.query(VectorEntity.vector_euclidean.nearest_neighbors([2.1, 2.1], 2)).build()
    assert query.count() == 2
    assert query.find_ids() == [2, 3]


def test_integer_scalars(test_store):
    box_test_entity = test_store.box(TestEntity)
    id1 = box_test_entity.put(TestEntity(int8=12, int16=12, int32=12, int64=12))
    id2 = box_test_entity.put(TestEntity(int8=45, int16=45, int32=45, int64=45))

    props = ["int8", "int16", "int32", "int64"]
    for p in props:
        prop = TestEntity._get_property(p)

        query = box_test_entity.query(prop.equals(12)).build()
        assert query.count() == 1
        assert query.find()[0].id == id1

        query = box_test_entity.query(prop.equals(45)).build()
        assert query.count() == 1
        assert query.find()[0].id == id2

        query = box_test_entity.query(prop.not_equals(12)).build()
        assert query.count() == 1
        assert query.find()[0].id == id2

        query = box_test_entity.query(prop.greater_than(12)).build()
        assert query.count() == 1
        assert query.find()[0].id == id2

        query = box_test_entity.query(prop.greater_or_equal(12)).build()
        assert query.count() == 2
        assert query.find()[0].id == id1
        assert query.find()[1].id == id2

        query = box_test_entity.query(prop.less_than(45)).build()
        assert query.count() == 1
        assert query.find()[0].id == id1

        query = box_test_entity.query(prop.less_or_equal(45)).build()
        assert query.count() == 2
        assert query.find()[0].id == id1
        assert query.find()[1].id == id2


def test_float_scalars(test_store):
    box_test_entity = test_store.box(TestEntity)
    id1 = box_test_entity.put(TestEntity(float32=12.3, float64=12.3))
    id2 = box_test_entity.put(TestEntity(float32=45.6, float64=45.6))
    id3 = box_test_entity.put(TestEntity(float32=45.7, float64=45.7))

    # Test int scalar literals
    props = ["float32", "float64"]
    for p in props:
        prop = TestEntity._get_property(p)

        # equals/not_equals should not exist 
        with pytest.raises(AttributeError):
            prop.equals(12)
        with pytest.raises(AttributeError):
            prop.not_equals(12)

        query = box_test_entity.query(prop.greater_or_equal(12)).build()
        assert query.count() == 3
        query = box_test_entity.query(prop.greater_than(13)).build()
        assert query.count() == 2
        assert query.find()[0].id == id2
        query = box_test_entity.query(prop.less_than(46)).build()
        assert query.count() == 3
        query = box_test_entity.query(prop.less_or_equal(45)).build()
        assert query.count() == 1
        query = box_test_entity.query(prop.between(10, 50)).build()
        assert query.count() == 3
        query = box_test_entity.query(prop.between(12, 13)).build()
        assert query.count() == 1
        query = box_test_entity.query(prop.between(12, 12)).build()
        assert query.count() == 0

    # Test float scalar literals 
    for p in props:
        prop = TestEntity._get_property(p)
        query = box_test_entity.query(prop.less_or_equal(12.299999)).build()
        assert query.count() == 0
        query = box_test_entity.query(prop.greater_than(12.3)).build()
        assert query.count() == 2
        query = box_test_entity.query(prop.greater_or_equal(12.3)).build()
        assert query.count() == 3
        query = box_test_entity.query(prop.less_than(45.6)).build()
        assert query.count() == 1
        query = box_test_entity.query(prop.less_or_equal(45.6)).build()
        assert query.count() == 2
        query = box_test_entity.query(prop.between(12.2, 12.4)).build()
        assert query.count() == 1
        query = box_test_entity.query(prop.between(45.5999, 45.61)).build()
        assert query.count() == 1
        query = box_test_entity.query(prop.between(45.5999, 45.7001)).build()
        assert query.count() == 2


def test_flex_contains_key_value(test_store):
    box = test_store.box(TestEntityFlex)
    box.put(TestEntityFlex(flex={"k1": "String", "k2": 2, "k3": "string"}))
    box.put(TestEntityFlex(flex={"k1": "strinG", "k2": 3, "k3": 10, "k4": [1, "foo", 3]}))
    box.put(TestEntityFlex(flex={"k1": "buzz", "k2": 3, "k3": [2, 3], "k4": {"k1": "a", "k2": "inner text"}}))
    box.put(TestEntityFlex(flex={"n1": "string", "n2": -7, "n3": [-10, 10], "n4": [4, 4, 4]}))
    box.put(TestEntityFlex(flex={"n1": "Apple", "n2": 3, "n3": [2, 3, 5], "n4": {"n1": [1, 2, "bar"]}}))

    assert box.count() == 5

    # Search case-sensitive = False
    query = box.query(TestEntityFlex.flex.contains_key_value("k1", "string", False)).build()
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
    query = box.query(TestEntityFlex.flex.contains_key_value("n1", "string", True)).build()
    results = query.find()
    assert len(results) == 1
    assert results[0].flex["n1"] == "string"
    assert results[0].flex["n2"] == -7
    assert results[0].flex["n3"] == [-10, 10]
    assert results[0].flex["n4"] == [4, 4, 4]

    # TODO Search using nested key (not supported yet)

    # No match (key)
    query = box.query(TestEntityFlex.flex.contains_key_value("missing key", "string", True)).build()
    assert len(query.find()) == 0

    # No match (value)
    query = box.query(TestEntityFlex.flex.contains_key_value("k1", "missing value", True)).build()
    assert len(query.find()) == 0


def test_offset_limit(test_store):
    box = test_store.box(TestEntity)
    box.put(TestEntity())
    box.put(TestEntity(str="a"))
    box.put(TestEntity(str="b"))
    box.put(TestEntity(str="c"))
    assert box.count() == 4

    int_prop = TestEntity.int64

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

    # Invalid values raise (a negative offset wrapped around in C: no results)
    for method in (query.offset, query.limit):
        with pytest.raises(IllegalArgumentError, match="must not be negative, got -1"):
            method(-1)
        for invalid in (1.5, "2", None, True):
            with pytest.raises(TypeError, match="must be an int"):
                method(invalid)
    assert len(query.find()) == 4  # Unchanged

    # Chaining: both return the query
    assert query.offset(1) is query
    assert query.limit(2) is query
    assert [o.str for o in query.offset(1).limit(2).find()] == ["a", "b"]


def test_null(test_store):
    box = test_store.box(TestEntity)
    id_none = box.put(TestEntity(str=None, int64=None, float64=None, date=None))  # null: put with None
    id_unset = box.put(TestEntity())  # unset: stored with default values, not null
    id_set = box.put(TestEntity(str="a", int64=1, float64=1.5, date=1700000000000))

    def ids(condition):
        return sorted(box.query(condition).build().find_ids())

    for prop in [TestEntity.str, TestEntity.int64, TestEntity.float64, TestEntity.date]:
        assert ids(prop.is_null()) == [id_none], prop.name
        assert ids(prop.is_not_null()) == [id_unset, id_set], prop.name
    # Null values read back as defaults, but do not match conditions on the default value
    assert box.get(id_none).str == ""
    assert ids(TestEntity.str.equals("")) == [id_unset]
    assert ids(TestEntity.int64.equals(0)) == [id_unset]
    # Combined, and via QueryBuilder
    assert ids(TestEntity.str.is_null() | TestEntity.str.equals("a")) == [id_none, id_set]
    assert ids(TestEntity.str.is_not_null() & TestEntity.int64.equals(0)) == [id_unset]
    qb = box.query()
    qb.is_null(TestEntity.int64)
    assert qb.build().find_ids() == [id_none]
    qb = box.query()
    qb.not_null("int64")
    assert sorted(qb.build().find_ids()) == [id_unset, id_set]


def test_any_all(test_store):
    box = test_store.box(TestEntity)

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


def test_set_parameter(test_store):
    box_test_entity = test_store.box(TestEntity)
    box_test_entity.put(TestEntity(str="Foo", int64=2, int32=703, int8=101))
    box_test_entity.put(TestEntity(str="FooBar", int64=10, int32=49, int8=45))
    box_test_entity.put(TestEntity(str="Bar", int64=10, int32=226, int8=126))
    box_test_entity.put(TestEntity(str="Foster", int64=2, int32=301, int8=42))
    box_test_entity.put(TestEntity(str="Fox", int64=10, int32=157, int8=11))
    box_test_entity.put(TestEntity(str="Barrakuda", int64=4, int32=386, int8=60))

    box_vector_entity = test_store.box(VectorEntity)
    box_vector_entity.put(VectorEntity(name="Object 1", vector_euclidean=[1, 1]))
    box_vector_entity.put(VectorEntity(name="Object 2", vector_euclidean=[2, 2]))
    box_vector_entity.put(VectorEntity(name="Object 3", vector_euclidean=[3, 3]))
    box_vector_entity.put(VectorEntity(name="Object 4", vector_euclidean=[4, 4]))
    box_vector_entity.put(VectorEntity(name="Object 5", vector_euclidean=[5, 5]))

    qb = box_test_entity.query()
    qb.starts_with_string("str", "fo", case_sensitive=False)
    qb.greater_than_int("int32", 150)
    qb.greater_than_int("int64", 0)
    query = qb.build()
    assert query.find_ids() == [1, 4, 5]

    # Test set_parameter_string
    query.set_parameter("str", "bar")
    assert query.find_ids() == [3, 6]

    # Test set_parameter_int
    query.set_parameter("int64", 8)
    assert query.find_ids() == [3]

    qb = box_vector_entity.query()
    qb.nearest_neighbors_f32("vector_euclidean", [3.4, 3.4], 3)
    query = qb.build()
    assert query.find_ids() == sorted([3, 4, 2])

    # Vector; an int sets the NN count
    query.set_parameter("vector_euclidean", [4.9, 4.9])
    assert query.find_ids() == sorted([5, 4, 3])

    query.set_parameter("vector_euclidean", [0, 0])
    assert query.find_ids() == sorted([1, 2, 3])

    query.set_parameter("vector_euclidean", [2.5, 2.1])
    assert query.find_ids() == sorted([2, 3, 1])

    query.set_parameter("vector_euclidean", 2)
    assert query.find_ids() == sorted([2, 3])


def test_set_parameter_alias(test_store):
    box = test_store.box(TestEntity)

    box.put(TestEntity(str="Foo", int64=2, int32=703, int8=101))
    box.put(TestEntity(str="FooBar", int64=10, int32=49, int8=45))

    box_vector = test_store.box(VectorEntity)
    box_vector.put(VectorEntity(name="Object 1", vector_euclidean=[1, 1]))
    box_vector.put(VectorEntity(name="Object 2", vector_euclidean=[2, 2]))
    box_vector.put(VectorEntity(name="Object 3", vector_euclidean=[3, 3]))
    box_vector.put(VectorEntity(name="Object 4", vector_euclidean=[4, 4]))
    box_vector.put(VectorEntity(name="Object 5", vector_euclidean=[5, 5]))

    str_prop = TestEntity.str
    int32_prop = TestEntity.int32
    int64_prop = TestEntity.int64

    # Test set parameter alias on string
    qb = box.query(str_prop.equals("Foo").alias("foo_filter"))
    query = qb.build()

    assert query.find()[0].str == "Foo"
    assert query.count() == 1

    query.set_parameter_alias("foo_filter", "FooBar")
    assert query.find()[0].str == "FooBar"
    assert query.count() == 1

    # Test set parameter alias on int64
    qb = box.query(int64_prop.greater_than(5).alias("greater_than_filter"))

    query = qb.build()
    assert query.count() == 1
    assert query.find()[0].str == "FooBar"

    assert query.set_parameter_alias("greater_than_filter", 1) is query

    assert query.count() == 2

    # Test set parameter alias on string/int32
    query = box.query(
        str_prop.equals("Foo").alias("str condition")
        .and_(int32_prop.greater_than(700).alias("int32 condition"))
    ).build()

    assert query.count() == 1
    assert query.find()[0].str == "Foo"

    assert query.set_parameter_alias("str condition", "FooBar") is query  # FooBar int32 isn't higher than 700 (49)
    assert query.count() == 0

    query.set_parameter_alias("int32 condition", 40)
    assert query.find()[0].str == "FooBar"

    # Test with &
    query = box.query(
        str_prop.equals("Foo").alias("str condition")
        & int32_prop.greater_than(700).alias("int32 condition")
    ).build()
    assert query.count() == 1

    # Test set parameter alias on vector
    vector_prop = VectorEntity.vector_euclidean

    query = box_vector.query(vector_prop.nearest_neighbors([3.4, 3.4], 3).alias("nearest_neighbour_filter")).build()
    assert query.count() == 3
    assert query.find_ids() == sorted([3, 4, 2])

    assert query.set_parameter_alias("nearest_neighbour_filter", [4.9, 4.9]) is query
    assert query.count() == 3
    assert query.find_ids() == sorted([5, 4, 3])


def test_set_parameter_alias_advanced(test_store):
    """ Tests set_parameter_alias in a complex scenario (i.e. multiple query conditions/logical aggregations). """

    # Setup 1
    box = test_store.box(TestEntity)
    box.put(TestEntity(str="Apple", bool=False, int64=47, int32=70))
    box.put(TestEntity(str="applE", bool=True, int64=253, int32=798))
    box.put(TestEntity(str="APPLE", bool=False, int64=3456, int32=123))
    box.put(TestEntity(str="Orange", bool=False, int64=2345, int32=53))
    box.put(TestEntity(str="orange", bool=True, int64=546, int32=5678))
    box.put(TestEntity(str="ORANGE", bool=True, int64=78, int32=798))
    box.put(TestEntity(str="oRANGE", bool=True, int64=89, int32=1234))
    box.put(TestEntity(str="Zucchini", bool=False, int64=1234, int32=9))
    assert box.count() == 8

    str_prop = TestEntity.str
    bool_prop = TestEntity.bool
    int32_prop = TestEntity.int32
    int64_prop = TestEntity.int64

    query = box.query(
        str_prop.equals("Dummy", case_sensitive=False).alias("str_filter")
        .and_(bool_prop.equals(False).alias("bool_filter"))
        .and_(
            int64_prop.greater_than(0).alias("int64_filter")
            .or_(int32_prop.less_than(100).alias("int32_filter"))
        )
    ).build()
    assert len(query.find_ids()) == 0

    # Test & and | without alias
    query = box.query(
        str_prop.equals("applE")
        | str_prop.equals("orange", case_sensitive=False) & bool_prop.equals(False)
    ).build()
    assert len(query.find_ids()) == 2

    # Test using & and | ops
    query = box.query(
        str_prop.equals("Dummy", case_sensitive=False).alias("str_filter")
        & bool_prop.equals(False).alias("bool_filter")
        & (
            int64_prop.greater_than(0).alias("int64_filter")
            | int32_prop.less_than(100).alias("int32_filter")
        )
    ).build()
    assert len(query.find_ids()) == 0

    query.set_parameter_alias("str_filter", "Apple")
    query.set_parameter_alias("int64_filter", 300)
    assert len(query.find_ids()) == 2  # Apple, APPLE

    query.set_parameter_alias("str_filter", "orange")
    query.set_parameter_alias("int64_filter", 1000)
    assert len(query.find_ids()) == 1  # Orange

    query.set_parameter_alias("str_filter", "Zucchini")
    assert len(query.find_ids()) == 1  # Zucchini

    # Bool and int32 parameters via the generic set_parameter_alias()
    query.set_parameter_alias("bool_filter", True)
    assert len(query.find_ids()) == 0  # Zucchini is False
    query.set_parameter_alias("str_filter", "orange")
    query.set_parameter_alias("int32_filter", 1000)
    assert len(query.find_ids()) == 1  # ORANGE (int32 798)
    query.set_parameter_alias("int64_filter", 500)
    assert len(query.find_ids()) == 2  # ORANGE, orange (int64 546)


# Bytes query
def test_bytes(test_store):
    box = test_store.box(TestEntity)

    bytes_prop = TestEntity.bytes

    id1 = box.put(TestEntity(bytes=bytes([9])))
    id2 = box.put(TestEntity(bytes=bytes([1, 0])))
    id3 = box.put(TestEntity(bytes=bytes([0, 1])))
    query = box.query(bytes_prop.greater_or_equal(bytes([0]))).build()
    assert query.count() == 3
    query = box.query(bytes_prop.greater_or_equal(bytes([1]))).build()
    assert query.count() == 2
    query = box.query(bytes_prop.greater_or_equal(bytes([9]))).build()
    assert query.count() == 1

    assert box.remove_all() == 3
    id1 = box.put(TestEntity(bytes=bytes([1, 2, 3, 4])))
    id2 = box.put(TestEntity(bytes=bytes([5, 6, 7, 8, 9, 10, 11])))
    query = box.query(bytes_prop.equals(bytes([1, 2, 3, 4]))).build()
    assert query.count() == 1
    assert query.find()[0].id == id1

    query = box.query(bytes_prop.greater_than(bytes([1, 2, 3, 4]))).build()
    assert query.count() == 1
    assert query.find()[0].id == id2

    query = box.query(bytes_prop.greater_or_equal(bytes([1, 2, 3, 4]))).build()
    assert query.count() == 2

    query = box.query(bytes_prop.greater_or_equal(bytes([0]))).build()
    assert query.count() == 2

    query = box.query(bytes_prop.less_than(bytes([5, 6, 7, 8, 9, 10, 11]))).build()
    assert query.count() == 1
    assert query.find()[0].id == id1

    query = box.query(bytes_prop.less_or_equal(bytes([5, 6, 7, 8, 9, 10, 11]))).build()
    assert query.count() == 2

    # bytes does not support not equals
    with pytest.raises(AttributeError):
        bytes_prop.not_equals(bytes([]))


def test_order(test_store):
    box = test_store.box(TestEntity)

    id1 = box.put(TestEntity(str="mango", int64=-423))
    id2 = box.put(TestEntity(str="apricot", int64=456))
    id3 = box.put(TestEntity(str="Apple", int64=5))
    id4 = box.put(TestEntity(str="Banana", int64=67))
    id5 = box.put(TestEntity(str="coconut", int64=2859))
    assert box.count() == 5

    # Order by int64 (ascending)
    query = box.query().order(TestEntity.int64).build()
    assert query.count() == 5
    assert [o.id for o in query.find()] == [id1, id3, id4, id2, id5]
    assert query.find_ids() == [id1, id3, id4, id2, id5]

    # Order by int64 (descending)
    query = box.query().order(TestEntity.int64, OrderFlags.DESCENDING).build()
    assert [o.id for o in query.find()] == [id5, id2, id4, id3, id1]
    assert query.find_ids() == [id5, id2, id4, id3, id1]
    query = box.query().order_desc(TestEntity.int64).build()
    assert query.find_ids() == [id5, id2, id4, id3, id1]

    # Order by int64 (unsigned ordering): -423 is the largest
    query = box.query().order(TestEntity.int64, OrderFlags.UNSIGNED).build()
    assert [o.id for o in query.find()] == [id3, id4, id2, id5, id1]

    # Order by str (case-insensitive)
    query = box.query().order(TestEntity.str).build()
    assert [o.str for o in query.find()] == ["Apple", "apricot", "Banana", "coconut", "mango"]

    # Order by str (case-sensitive)
    query = box.query().order(TestEntity.str, OrderFlags.CASE_SENSITIVE).build()
    assert [o.str for o in query.find()] == ["Apple", "Banana", "apricot", "coconut", "mango"]

    # Combined flags; property given by name
    query = box.query().order("str", OrderFlags.CASE_SENSITIVE | OrderFlags.DESCENDING).build()
    assert [o.str for o in query.find()] == ["mango", "coconut", "apricot", "Banana", "Apple"]
    query = box.query().order_desc("str", OrderFlags.CASE_SENSITIVE).build()
    assert [o.str for o in query.find()] == ["mango", "coconut", "apricot", "Banana", "Apple"]

    # With a condition, offset and limit
    query = box.query(TestEntity.int64.greater_than(0)).order(TestEntity.str).build()
    assert [o.str for o in query.find()] == ["Apple", "apricot", "Banana", "coconut"]
    query.offset(1)
    query.limit(2)
    assert [o.str for o in query.find()] == ["apricot", "Banana"]

    # TODO test NULLS_LAST/NULLS_ZERO when None values will be supported (i.e. optional properties)


def test_order_multiple(test_store):
    box = test_store.box(TestEntity)

    id1 = box.put(TestEntity(str="b", int64=1))
    id2 = box.put(TestEntity(str="a", int64=2))
    id3 = box.put(TestEntity(str="B", int64=0))
    id4 = box.put(TestEntity(str="a", int64=3))

    # The first order is the primary one; the second one orders within equal values ("b" == "B" by default)
    query = box.query().order(TestEntity.str).order(TestEntity.int64, OrderFlags.DESCENDING).build()
    assert query.find_ids() == [id4, id2, id1, id3]

    query = box.query().order(TestEntity.str).order(TestEntity.int64).build()
    assert query.find_ids() == [id2, id4, id3, id1]


def test_remove(test_store):
    box = test_store.box(TestEntity)

    box.put(TestEntity(str="Object 1", int64=3))
    box.put(TestEntity(str="Object 2", int64=43))
    box.put(TestEntity(str="Object 3", int64=534))
    box.put(TestEntity(str="Object 4", int64=234))
    box.put(TestEntity(str="Object 5", int64=56))
    assert box.count() == 5

    query = box.query(TestEntity.int64.less_than(500)).build()
    assert query.remove() == 4

    assert box.count() == 1


def test_string_one_of(test_store):
    box = test_store.box(TestEntity)

    box.put(TestEntity(str="Apple"))
    box.put(TestEntity(str="banana"))
    box.put(TestEntity(str="Peach"))
    box.put(TestEntity(str="MANGO"))
    box.put(TestEntity(str="Strawberry"))
    assert box.count() == 5

    query = box.query(TestEntity.str.one_of(["Apple", "Banana", "Peach"])).build()
    objects = query.find()
    assert len(objects) == 2
    assert objects[0].str == "Apple"
    assert objects[1].str == "Peach"

    query = box.query(TestEntity.str.one_of(["Apple", "Banana", "Peach"], case_sensitive=False)).build()
    objects = query.find()
    assert len(objects) == 3
    assert objects[0].str == "Apple"
    assert objects[1].str == "banana"
    assert objects[2].str == "Peach"

    query = box.query(TestEntity.str.one_of(["MANGO"])).build()
    objects = query.find()
    assert len(objects) == 1
    assert objects[0].str == "MANGO"

    query = box.query(TestEntity.str.one_of([])).build()
    assert query.count() == 0


def test_contains_string(test_store):
    box = test_store.box(TestEntity)

    box.put(TestEntity(str="Green apple"))
    box.put(TestEntity(str="Red Apple"))
    box.put(TestEntity(str="Rotten apple"))
    box.put(TestEntity(str="Banana"))
    assert box.count() == 4

    query = box.query(TestEntity.str.contains("apple")).build()
    objects = query.find()
    assert len(objects) == 2
    assert objects[0].str == "Green apple"
    assert objects[1].str == "Rotten apple"

    query = box.query(TestEntity.str.contains("apple", case_sensitive=False)).build()
    objects = query.find()
    assert len(objects) == 3
    assert objects[0].str == "Green apple"
    assert objects[1].str == "Red Apple"
    assert objects[2].str == "Rotten apple"

    query = box.query(TestEntity.str.contains("pear")).build()
    assert query.count() == 0


def test_int_one_of(test_store):
    box = test_store.box(TestEntity)

    id1 = box.put(TestEntity(int32=1, int64=-10, date=1000))
    id2 = box.put(TestEntity(int32=2, int64=20, date=2000))
    id3 = box.put(TestEntity(int32=3, int64=2 ** 40, date=3000))
    id4 = box.put(TestEntity(int32=-4, int64=40, date=4000))

    # Int32 uses the 32-bit C API variant, the others the 64-bit one
    assert box.query(TestEntity.int32.one_of([1, 3, 5])).build().find_ids() == [id1, id3]
    assert box.query(TestEntity.int32.not_one_of([1, 3, 5])).build().find_ids() == [id2, id4]
    assert box.query(TestEntity.int64.one_of([-10, 2 ** 40])).build().find_ids() == [id1, id3]
    assert box.query(TestEntity.int64.not_one_of([-10, 2 ** 40])).build().find_ids() == [id2, id4]
    assert box.query(TestEntity.id.one_of([id2, id4])).build().find_ids() == [id2, id4]
    assert box.query(TestEntity.date.one_of([2000, 4000])).build().find_ids() == [id2, id4]

    # Tuples are accepted as well; combined with other conditions
    query = box.query(TestEntity.int32.one_of((1, 2, 3)) & TestEntity.int64.greater_than(0)).build()
    assert query.find_ids() == [id2, id3]

    # Empty lists: nothing is "in" it; everything is "not in" it
    assert box.query(TestEntity.int64.one_of([])).build().count() == 0
    assert box.query(TestEntity.int64.not_one_of([])).build().count() == 4

    # Not supported by the C API for 8/16-bit integers and bools
    with pytest.raises(TypeError):
        TestEntity.int8.one_of([1])
    with pytest.raises(TypeError):
        TestEntity.int16.not_one_of([1])
    with pytest.raises(TypeError):
        TestEntity.bool.one_of([True])


def test_set_parameter_one_of(test_store):
    box = test_store.box(TestEntity)

    id1 = box.put(TestEntity(str="Apple", int32=1, int64=10))
    id2 = box.put(TestEntity(str="Banana", int32=2, int64=20))
    id3 = box.put(TestEntity(str="Cherry", int32=3, int64=30))

    # Via property
    query = box.query(TestEntity.str.one_of(["Apple"])).build()
    assert query.find_ids() == [id1]
    assert query.set_parameter(TestEntity.str, ["Banana", "Cherry"]).find_ids() == [id2, id3]
    assert query.set_parameter(TestEntity.str, []).count() == 0

    query = box.query(TestEntity.int32.one_of([1])).build()
    assert query.set_parameter(TestEntity.int32, [2, 3]).find_ids() == [id2, id3]
    query = box.query(TestEntity.int64.not_one_of([10])).build()
    assert query.set_parameter("int64", [10, 20]).find_ids() == [id3]

    # Via alias; int32 and int64 conditions need different C API calls
    query = box.query(TestEntity.str.one_of(["Apple"], case_sensitive=False).alias("names")
                      & TestEntity.int32.one_of([1]).alias("ints32")
                      | TestEntity.int64.one_of([]).alias("ints64")).build()
    assert query.find_ids() == [id1]
    query.set_parameter_alias("names", ["BANANA", "cherry"])
    assert query.find_ids() == []
    query.set_parameter_alias("ints32", [2, 3])
    assert query.find_ids() == [id2, id3]
    query.set_parameter_alias("names", [])
    query.set_parameter_alias("ints64", [10])
    assert query.find_ids() == [id1]


def test_set_parameter_generic(test_store):
    """ set_parameter()/set_parameter_alias() choose the kind of parameter by the property type. """
    box = test_store.box(TestEntity)
    id1 = box.put(TestEntity(str="Apple", int32=1, int64=10))
    id2 = box.put(TestEntity(str="Banana", int32=2, int64=20))
    id3 = box.put(TestEntity(str="Cherry", int32=3, int64=30))

    query = box.query(TestEntity.str.equals("Apple") & TestEntity.int64.greater_than(0)).build()
    assert query.set_parameter(TestEntity.str, "Banana").find_ids() == [id2]
    assert query.set_parameter("int64", 20).find_ids() == []

    query = box.query(TestEntity.str.one_of(["Apple"]) & TestEntity.int32.one_of([1, 2, 3])).build()
    assert query.set_parameter(TestEntity.str, ["Banana", "Cherry"]).find_ids() == [id2, id3]
    assert query.set_parameter(TestEntity.int32, [3]).find_ids() == [id3]
    assert query.set_parameter(TestEntity.str, []).count() == 0  # The property type decides: strings

    # Aliases; the int32 and int64 "one of" conditions need different C API calls
    query = box.query(TestEntity.str.equals("Apple").alias("name")
                      | TestEntity.int32.one_of([]).alias("ints32")
                      | TestEntity.int64.one_of([]).alias("ints64")).build()
    assert query.find_ids() == [id1]
    assert query.set_parameter_alias("name", "Cherry").find_ids() == [id3]
    assert query.set_parameter_alias("ints32", [2]).find_ids() == [id2, id3]
    assert query.set_parameter_alias("ints64", [10]).find_ids() == [id1, id2, id3]

    assert "Cherry" in query.describe_parameters()

    # Wrong value types
    with pytest.raises(TypeError):
        query.set_parameter(TestEntity.int64, "1")
    with pytest.raises(TypeError):
        query.set_parameter(TestEntity.int64, [1.5])
    with pytest.raises(TypeError):
        query.set_parameter(TestEntity.str, ["a", 1])
    with pytest.raises(TypeError):
        query.set_parameter_alias("name", 1.5)

    # Vector: a list sets the search vector, an integer the maximum result count
    vector_box = test_store.box(VectorEntity)
    for i in range(1, 6):
        vector_box.put(VectorEntity(name=f"Object {i}", vector_euclidean=[i, i]))
    query = vector_box.query(VectorEntity.vector_euclidean.nearest_neighbors([3.4, 3.4], 3).alias("nn")).build()
    assert sorted(query.find_ids()) == [2, 3, 4]
    assert sorted(query.set_parameter(VectorEntity.vector_euclidean, [4.9, 4.9]).find_ids()) == [3, 4, 5]
    assert sorted(query.set_parameter("vector_euclidean", 2).find_ids()) == [4, 5]
    assert sorted(query.set_parameter_alias("nn", [0, 0]).find_ids()) == [1, 2]

    # Alias set directly on the QueryBuilder: the property is unknown, so the value type (and for lists, the C type
    # size: 0 for vectors) decides
    qb = vector_box.query()
    qb.nearest_neighbors_f32("vector_euclidean", [3.4, 3.4], 3)
    qb.alias("qb_nn")
    query = qb.build()
    assert sorted(query.set_parameter_alias("qb_nn", [0.0, 0.0]).find_ids()) == [1, 2, 3]
    assert sorted(query.set_parameter_alias("qb_nn", [5, 5]).find_ids()) == [3, 4, 5]
    import numpy as np
    with pytest.raises(TypeError):
        query.set_parameter_alias("qb_nn", np.array([5, 5], dtype=np.float64))
    qb = box.query()
    qb.in_ints("int32", [1])
    qb.alias("qb_ints32")
    qb.in_strings("str", ["Apple"])
    qb.alias("qb_names")
    query = qb.build()
    assert query.set_parameter_alias("qb_ints32", [2, 3]).set_parameter_alias("qb_names", []).find_ids() == []
    assert query.set_parameter_alias("qb_names", ["Banana", "Cherry"]).find_ids() == [id2, id3]


def test_set_parameter_types(test_store):
    """ set_parameter() for float, bytes and date properties; set_parameters() for between(). """
    box = test_store.box(TestEntity)
    jan = datetime(2024, 1, 1, tzinfo=timezone.utc)
    feb = datetime(2024, 2, 1, tzinfo=timezone.utc)
    mar = datetime(2024, 3, 1, tzinfo=timezone.utc)
    id1 = box.put(TestEntity(int64=10, float64=1.5, float32=1.5, bytes=bytes([1]), date=jan, date_nano=1))
    id2 = box.put(TestEntity(int64=20, float64=2.5, float32=2.5, bytes=bytes([2]), date=feb, date_nano=2))
    id3 = box.put(TestEntity(int64=30, float64=3.5, float32=3.5, bytes=bytes([3]), date=mar, date_nano=3))

    # Floating point: a single value (also given as int) and two values
    for prop in (TestEntity.float64, TestEntity.float32):
        query = box.query(prop.greater_than(0.0)).build()
        assert query.set_parameter(prop, 2.0).find_ids() == [id2, id3]
        assert query.set_parameter(prop, 3).find_ids() == [id3]
        query = box.query(prop.between(0.0, 10.0).alias("range")).build()
        assert query.set_parameters(prop, 1.0, 3.0).find_ids() == [id1, id2]
        assert query.set_parameters_alias("range", 2, 4).find_ids() == [id2, id3]
        with pytest.raises(TypeError):
            query.set_parameter(prop, "1")

    # Integers: two values
    query = box.query(TestEntity.int64.between(0, 100).alias("range")).build()
    assert query.set_parameters(TestEntity.int64, 15, 25).find_ids() == [id2]
    assert query.set_parameters_alias("range", 20, 30).find_ids() == [id2, id3]
    assert "20" in query.describe_parameters() and "30" in query.describe_parameters()
    with pytest.raises(TypeError):
        query.set_parameters(TestEntity.int64, 1.5, 2)
    with pytest.raises(TypeError):
        query.set_parameters(TestEntity.str, "a", "b")

    # Bytes
    query = box.query(TestEntity.bytes.equals(bytes([1])).alias("bytes")).build()
    assert query.set_parameter(TestEntity.bytes, bytes([2])).find_ids() == [id2]
    assert query.set_parameter_alias("bytes", bytearray([3])).find_ids() == [id3]
    with pytest.raises(TypeError):
        query.set_parameter(TestEntity.int64, bytes([1]))

    # Dates: datetime, float (seconds) or int (milliseconds; nanoseconds for DateNano)
    query = box.query(TestEntity.date.greater_than(0)).build()
    assert query.set_parameter(TestEntity.date, jan).find_ids() == [id2, id3]
    assert query.set_parameter(TestEntity.date, feb.timestamp()).find_ids() == [id3]
    assert query.set_parameter(TestEntity.date, int(jan.timestamp() * 1000) - 1).find_ids() == [id1, id2, id3]
    query = box.query(TestEntity.date.between(0, 0)).build()
    assert query.set_parameters(TestEntity.date, jan, feb).find_ids() == [id1, id2]
    query = box.query(TestEntity.date.one_of([0])).build()
    assert query.set_parameter(TestEntity.date, [jan, mar]).find_ids() == [id1, id3]
    query = box.query(TestEntity.date_nano.equals(0).alias("nano")).build()
    assert query.set_parameter_alias("nano", 2).find_ids() == [id2]
    with pytest.raises(TypeError):
        query.set_parameter(TestEntity.int64, jan)

    # Alias set via QueryBuilder.alias(): the value decides
    qb = box.query()
    qb.greater_than_double("float64", 0.0)
    qb.alias("qb_float")
    query = qb.build()
    assert query.set_parameter_alias("qb_float", 2.0).find_ids() == [id2, id3]
    with pytest.raises(TypeError):
        query.set_parameter_alias("qb_float", jan)  # Unknown whether milliseconds or nanoseconds


def test_query_close(test_store):
    box = test_store.box(TestEntity)
    box.put(TestEntity(str="foo"))
    query = box.query(TestEntity.str.equals("foo")).build()
    assert not query.is_closed()
    assert query.count() == 1
    query.close()
    assert query.is_closed()
    query.close()  # Closing again does nothing
    for use in (query.find, query.find_ids, query.count, query.remove, query.describe_parameters,
                lambda: query.offset(1), lambda: query.set_parameter(TestEntity.str, "bar")):
        with pytest.raises(IllegalStateError, match="The query is closed"):
            use()
    assert box.count() == 1

    with box.query(TestEntity.str.equals("foo")).build() as query:
        assert query.count() == 1
    assert query.is_closed()

    # Closed also if the with block raises
    with pytest.raises(ValueError):
        with box.query().build() as query:
            raise ValueError()
    assert query.is_closed()


def test_query_builder_closed_by_build(test_store):
    box = test_store.box(TestEntity)
    box.put(TestEntity(str="foo"))
    qb = box.query(TestEntity.str.equals("foo"))
    query = qb.build()
    message = r"The query builder is closed: build\(\) closes it"
    with pytest.raises(IllegalStateError, match=message):
        qb.build()
    with pytest.raises(IllegalStateError, match=message):
        qb.order(TestEntity.str)
    with pytest.raises(IllegalStateError, match=message):
        qb.alias("x")
    qb.close()  # Does nothing
    assert query.count() == 1

    # Closing a builder that is not built
    qb = box.query(TestEntity.str.equals("foo"))
    qb.close()
    with pytest.raises(IllegalStateError, match=message):
        qb.build()
    with pytest.raises(IllegalStateError, match=message):
        qb.equals_string(TestEntity.str, "foo", True)


def test_query_native_resources_closed(test_store, monkeypatch):
    """ Queries and query builders free their native resources: build() closes the builder, a query is closed when
    garbage collected (or closed explicitly). """
    import gc
    import objectbox.query
    import objectbox.query_builder
    closed = {"query": 0, "builder": 0}
    query_close, qb_close = objectbox.query.obx_query_close, objectbox.query_builder.obx_qb_close

    def count_query_close(c_query):
        closed["query"] += 1
        return query_close(c_query)

    def count_qb_close(c_builder):
        closed["builder"] += 1
        return qb_close(c_builder)

    monkeypatch.setattr(objectbox.query, "obx_query_close", count_query_close)
    monkeypatch.setattr(objectbox.query_builder, "obx_qb_close", count_qb_close)
    box = test_store.box(TestEntity)
    box.put(TestEntity(str="foo"))
    for i in range(100):
        assert box.query(TestEntity.str.equals("foo")).build().count() == 1
        box.query(TestEntity.str.equals("foo"))  # Never built
    gc.collect()
    assert closed == {"query": 100, "builder": 200}
    assert len(test_store._native_resources) == 0


def test_query_store_closed(test_store):
    box = test_store.box(TestEntity)
    box.put(TestEntity(str="foo"))
    query = box.query(TestEntity.str.equals("foo")).build()
    qb = box.query(TestEntity.str.equals("foo"))
    test_store.close()
    assert query.is_closed()  # Closed before the store
    with pytest.raises(IllegalStateError, match="Store is closed"):
        query.count()
    with pytest.raises(IllegalStateError, match="Store is closed"):
        qb.build()


def test_nearest_neighbors(test_store):
    """ nearest_neighbors(query_vector, max_result_count), named like in the other ObjectBox languages;
    nearest_neighbor() is deprecated. """
    box = test_store.box(VectorEntity)
    for i in range(1, 6):
        box.put(VectorEntity(name="Object %d" % i, vector_euclidean=[i, i]))
    prop = VectorEntity.vector_euclidean
    query = box.query(prop.nearest_neighbors(query_vector=[2.1, 2.1], max_result_count=2)).build()
    assert [o.name for o, score in query.find_with_scores()] == ["Object 2", "Object 3"]

    with pytest.warns(DeprecationWarning, match=r"nearest_neighbor\(\) is deprecated, use nearest_neighbors\(\)"):
        condition = prop.nearest_neighbor([2.1, 2.1], 3)
    query = box.query(condition).build()
    assert [o.name for o, score in query.find_with_scores()] == ["Object 2", "Object 3", "Object 1"]


def test_find_first_unique(test_store):
    box = test_store.box(TestEntity)
    box.put([TestEntity(str="b", int64=2), TestEntity(str="a", int64=1), TestEntity(str="a", int64=3)])

    assert box.query().build().find_first().str == "b"  # By ID
    assert box.query().order(TestEntity.int64).build().find_first().int64 == 1
    assert box.query().order_desc(TestEntity.int64).build().find_first().int64 == 3
    assert box.query(TestEntity.str.equals("a")).build().find_first().int64 == 1
    assert box.query(TestEntity.str.equals("x")).build().find_first() is None

    assert box.query(TestEntity.str.equals("b")).build().find_unique().int64 == 2
    assert box.query(TestEntity.str.equals("x")).build().find_unique() is None
    query = box.query(TestEntity.str.equals("a")).build()
    with pytest.raises(NonUniqueResultError):
        query.find_unique()
    assert query.set_parameter(TestEntity.str, "b").find_unique().int64 == 2  # The query can still be used

    # Within a transaction (uses it)
    with test_store.read_tx():
        assert box.query(TestEntity.int64.equals(3)).build().find_first().str == "a"


def test_date_conditions_datetime(test_store):
    """ Date and DateNano conditions take a datetime or float seconds, like put() (only ints failed with a plain
    Exception before); ints are milliseconds or nanoseconds. """
    from datetime import timedelta
    box = test_store.box(TestEntityDatetime)
    base = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
    ids = box.put([TestEntityDatetime(date=(base + timedelta(days=i)).timestamp(), date_nano=base + timedelta(days=i))
                   for i in range(3)])

    def find(condition):
        return box.query(condition).build().find_ids()

    for prop in (TestEntityDatetime.date, TestEntityDatetime.date_nano):
        assert find(prop.equals(base)) == [ids[0]]
        assert find(prop.not_equals(base)) == ids[1:]
        assert find(prop.greater_than(base)) == ids[1:]
        assert find(prop.greater_or_equal(base + timedelta(days=1))) == ids[1:]
        assert find(prop.less_than(base + timedelta(hours=1))) == [ids[0]]
        assert find(prop.less_or_equal(base + timedelta(days=1))) == ids[:2]
        assert find(prop.between(base + timedelta(hours=1), base + timedelta(days=2))) == ids[1:]
        assert find(prop.one_of([base, base + timedelta(days=2)])) == [ids[0], ids[2]]
        assert find(prop.not_one_of([base])) == ids[1:]
        assert find(prop.equals(base.timestamp())) == [ids[0]]  # float: seconds
    ms = int(base.timestamp()) * 1000
    assert find(TestEntityDatetime.date.equals(ms)) == [ids[0]]  # int: milliseconds
    assert find(TestEntityDatetime.date_nano.equals(ms * 1000000)) == [ids[0]]  # int: nanoseconds

    # The query parameter takes the same values
    query = box.query(TestEntityDatetime.date.equals(base)).build()
    assert query.set_parameter(TestEntityDatetime.date, base + timedelta(days=2)).find_ids() == [ids[2]]

    with pytest.raises(TypeError):
        TestEntityDatetime.date.equals("2026-01-01")


def test_scores_named_tuples(test_store):
    """ Scored results are named tuples with the attribute names of Dart (ObjectWithScore.object/.score,
    IdWithScore.id/.score); unpacking and comparing like plain tuples still works. """
    box = test_store.box(VectorEntity)
    for i in range(1, 4):
        box.put(VectorEntity(name="Object %d" % i, vector_euclidean=[i, i]))
    query = box.query(VectorEntity.vector_euclidean.nearest_neighbors([1.0, 1.0], 2)).build()

    results = query.find_with_scores()
    assert all(isinstance(result, objectbox.ObjectWithScore) for result in results)
    assert [(r.object.name, r.score) for r in results] == [("Object 1", 0.0), ("Object 2", 2.0)]
    obj, score = results[1]
    assert obj.name == "Object 2" and score == 2.0

    id_results = query.find_ids_with_scores()
    assert all(isinstance(result, objectbox.IdWithScore) for result in id_results)
    assert [(r.id, r.score) for r in id_results] == [(1, 0.0), (2, 2.0)]
    assert id_results == [(1, 0.0), (2, 2.0)]  # Equal to plain tuples


def test_describe(test_store):
    query = test_store.box(TestEntity).query(TestEntity.str.equals("x") & TestEntity.int64.greater_than(3)).build()
    description = query.describe()
    assert description.startswith("Query for entity TestEntity with 3 conditions")
    assert "int64" in description and "str" in description
    assert query.describe_parameters() == '(str == "x"\n AND int64 > 3)'


def test_query_builder_alias_property(test_store):
    """ QueryBuilder.alias() remembers the property of the last condition, so set_parameter_alias() sets the value by
    the property's type, e.g. a datetime for a Date (was inferred from the value: datetime was rejected). """
    from datetime import timedelta
    box = test_store.box(TestEntityDatetime)
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    ids = box.put([TestEntityDatetime(date=(base + timedelta(days=i)).timestamp()) for i in range(3)])

    qb = box.query()
    qb.greater_than_int(TestEntityDatetime.date, int(base.timestamp() * 1000))
    qb.alias("after")
    query = qb.build()
    assert query.find_ids() == ids[1:]
    assert query.set_parameter_alias("after", base + timedelta(days=1)).find_ids() == [ids[2]]

    # A float property: an int value is converted by the property type
    test_box = test_store.box(TestEntity)
    test_box.put([TestEntity(float64=1.5), TestEntity(float64=3.5)])
    qb = test_box.query()
    qb.greater_than_double(TestEntity.float64, 1.0)
    qb.alias("min")
    query = qb.build()
    assert len(query.find()) == 2
    assert [o.float64 for o in query.set_parameter_alias("min", 2).find()] == [3.5]
