"""Experimental fast FlatBuffers builder and codegen: the bytes must equal those of the generic flatbuffers.Builder
(reference)."""
import linecache
import math
import random
from datetime import datetime, timezone

import numpy as np
import pytest

from objectbox import experimental, Entity, Id, Int32, Int64, Model, Store, String, Float32Vector, Int64Vector, Bytes
from objectbox.model.codegen import CodegenBuilder
from objectbox.model.fast_builder import FastBuilder
from tests.common import create_test_store
from tests.model import TestEntity, TestEntityDatetime, TestEntityFlex, VectorEntity


@pytest.fixture
def fast_builder_state():
    """Restores the experimental switches (e.g. as set for the whole test suite) after a test that changes them."""
    saved = (experimental._flatbuffers_mode, experimental._flatbuffers_verify)
    yield
    experimental._flatbuffers_mode, experimental._flatbuffers_verify = saved


# The experimental switches per mode, e.g. for tests running with each builder
ENABLE = {
    experimental.FAST_BUILDER: experimental.enable_fast_flatbuffers_builder,
    experimental.CODEGEN: experimental.enable_flatbuffers_codegen,
}


def assert_same_bytes(entity, obj, id=1):
    """Checks both the fast builder and codegen against the reference."""
    reference = bytes(entity._marshal_builder(obj, id))
    fast = FastBuilder(entity).marshal(obj, id)
    assert fast.hex() == reference.hex()  # hex: readable diff on failure
    generated = CodegenBuilder(entity).marshal(obj, id)
    assert generated.hex() == reference.hex()
    return reference


def complex_object(**overrides) -> TestEntity:
    """A TestEntity with all properties set (all property types)."""
    values = dict(str="foo bar", bool=True, int64=-1234567890123, int32=-123456, int16=-1234, int8=-12,
                  float64=1.2345678901, float32=1.5, bools=np.array([True, False, True]), bytes=b"\x00\x01\xff",
                  shorts=np.array([1, -2, 3]), chars=np.array([65, 66, 0xFFFF]), ints=np.array([1, -2, 3, 4, 5]),
                  longs=np.array([2 ** 40, -(2 ** 40)]), floats=np.array([1.5, -2.5]), doubles=np.array([0.1, 0.2]),
                  bools_list=[True, False], shorts_list=[-1, 2], chars_list=[0x41, 0x2603], ints_list=[1, 2, 3],
                  longs_list=[2 ** 50], floats_list=[0.5], doubles_list=[1e300, -1e-300], date=1700000000123,
                  date_nano=1700000000123456789, flex={"a": [1, "b", None], "c": {"d": 2.5}})
    values.update(overrides)
    return TestEntity(**values)


def test_complex_object(test_store):
    assert_same_bytes(TestEntity, complex_object(), id=123456789)


def test_unset_properties(test_store):
    # Unset properties are written as default values (0, "", empty vectors; Flex: null); there are no nulls
    assert_same_bytes(TestEntity, TestEntity())
    assert_same_bytes(TestEntityDatetime, TestEntityDatetime())
    assert_same_bytes(TestEntityFlex, TestEntityFlex())
    assert_same_bytes(VectorEntity, VectorEntity())


def test_partially_set(test_store):
    assert_same_bytes(TestEntity, TestEntity(str="only a string"))
    assert_same_bytes(TestEntity, TestEntity(int8=1, doubles=np.array([1.0])))
    assert_same_bytes(VectorEntity, VectorEntity(name="v", vector_cosine=[0.5, 0.5]))


def test_strings(test_store):
    for text in ["", "a", "äöü ✓ 日本語 🦆", "x" * 1000, "with\0nul"]:
        assert_same_bytes(TestEntity, TestEntity(str=text))


def test_empty_vectors(test_store):
    assert_same_bytes(TestEntity, complex_object(bools=np.array([]), shorts=[], chars=np.array([]), ints=[], longs=[],
                                                 floats=np.array([]), doubles=[], bools_list=[], longs_list=[],
                                                 bytes=b"", flex=[]))


def test_numeric_limits(test_store):
    assert_same_bytes(TestEntity, TestEntity(int8=-128, int16=-2 ** 15, int32=-2 ** 31, int64=-2 ** 63))
    assert_same_bytes(TestEntity, TestEntity(int8=127, int16=2 ** 15 - 1, int32=2 ** 31 - 1, int64=2 ** 63 - 1))
    for value in [math.nan, math.inf, -math.inf, -0.0, 3.4e38, 5e-324]:
        assert_same_bytes(TestEntity, TestEntity(float64=value, float32=value if abs(value) < 1e39 else 0.0,
                                                 doubles=[value]))
    assert_same_bytes(TestEntity, TestEntity(id=0), id=2 ** 63 - 1)


def test_dates(test_store):
    now = datetime.now(timezone.utc)
    assert_same_bytes(TestEntityDatetime, TestEntityDatetime(date=now, date_nano=now))
    assert_same_bytes(TestEntityDatetime, TestEntityDatetime(date=1.5, date_nano=datetime(1970, 1, 1, tzinfo=timezone.utc)))


def test_flex_values(test_store):
    for value in [None, 0, -1, 2.5, "text", b"bytes", [1, [2, [3]]], {"k": {"l": [True, False]}}]:
        assert_same_bytes(TestEntityFlex, TestEntityFlex(flex=value))


def test_alignment_combinations(test_store):
    """Lengths of strings and vectors determine the padding; this sweeps many combinations (all residues mod 8)."""
    rng = random.Random(42)
    for i in range(500):
        n = lambda: rng.randrange(0, 18)
        obj = TestEntity(str="s" * n(), bytes=bytes(n()), bools=[True] * n(), shorts=list(range(n())),
                         chars=list(range(n())), ints=list(range(n())), longs=list(range(n())),
                         floats=[0.5] * n(), doubles=[0.25] * n(), flex="f" * n())
        assert_same_bytes(TestEntity, obj, id=i + 1)
        assert_same_bytes(VectorEntity, VectorEntity(name="n" * n(), vector_euclidean=[1.0] * n()), id=i + 1)


def test_property_id_gaps(tmp_path):
    """Removed properties leave unused FlatBuffers slots: in between (zero vtable entries) and at the end (trimmed)."""
    json_file = str(tmp_path / "model.json")

    def store_for(entity_class):
        model = Model()
        model.entity(entity_class)
        return Store(model=model, directory=str(tmp_path / "db"), model_json_file=json_file)

    @Entity(model="fast-fb-gaps-1")
    class GapEntity:
        id = Id
        a = String
        b = Int32
        c = Int64Vector
        d = Bytes

    store_for(GapEntity).close()

    @Entity(model="fast-fb-gaps-2")
    class GapEntity:  # b removed: gap in the middle
        id = Id
        a = String
        c = Int64Vector
        d = Bytes

    store = store_for(GapEntity)
    assert GapEntity._last_property_iduid.id == 5 and [p.id for p in GapEntity._properties] == [1, 2, 4, 5]
    assert_same_bytes(GapEntity, GapEntity(a="text", c=[1, 2], d=b"x"))
    store.close()

    @Entity(model="fast-fb-gaps-3")
    class GapEntity:  # c and d removed as well: unused slots at the end
        id = Id
        a = String

    store = store_for(GapEntity)
    assert GapEntity._last_property_iduid.id == 5 and [p.id for p in GapEntity._properties] == [1, 2]
    assert_same_bytes(GapEntity, GapEntity(a="text"))
    store.close()


def test_none_values(test_store):
    # No null support: None fails in all builders
    for obj in [TestEntity(str=None), TestEntity(int32=None), TestEntity(longs=[None])]:
        with pytest.raises(Exception):
            TestEntity._marshal_builder(obj, 1)
        with pytest.raises(Exception):
            FastBuilder(TestEntity).marshal(obj, 1)
        with pytest.raises(Exception):
            CodegenBuilder(TestEntity).marshal(obj, 1)


@pytest.mark.parametrize("mode", ENABLE)
def test_invalid_values_raise_reference_errors(test_store, fast_builder_state, mode):
    # With an experimental builder enabled, invalid values raise the same errors as without it
    for obj in [TestEntity(int8=128), TestEntity(int32=2 ** 31), TestEntity(bool=2), TestEntity(int64=1.5),
                TestEntity(str=None), TestEntity(bytes="not bytes")]:
        experimental._flatbuffers_mode = None
        with pytest.raises(Exception) as reference:
            TestEntity._marshal(obj, 1)
        ENABLE[mode](True)
        with pytest.raises(reference.type):
            TestEntity._marshal(obj, 1)
        ENABLE[mode](True, verify=True)  # as in the test suite with the switch
        with pytest.raises(reference.type):
            TestEntity._marshal(obj, 1)


@pytest.mark.parametrize("mode", ENABLE)
def test_put_get_round_trip(fast_builder_state, mode):
    ENABLE[mode](True, verify=True)
    store = create_test_store()
    try:
        box = store.box(TestEntity)
        objects = [complex_object(str=f"object {i}", int32=i) for i in range(100)] + [TestEntity()]
        box.put(objects)
        box.put(complex_object(str="single"))
        read = box.get_all()
        assert len(read) == 102
        assert [o.str for o in read] == [f"object {i}" for i in range(100)] + ["", "single"]
        assert read[0].flex == {"a": [1, "b", None], "c": {"d": 2.5}}
        assert list(read[1].longs) == [2 ** 40, -(2 ** 40)]
        # The C library reads the stored FlatBuffers for queries
        query = box.query(TestEntity.str.equals("object 42") & TestEntity.int32.equals(42)).build()
        assert [o.id for o in query.find()] == [43]
    finally:
        store.close()


def test_switch(test_store, fast_builder_state):
    experimental.enable_fast_flatbuffers_builder(False)
    experimental.enable_flatbuffers_codegen(False)
    assert not experimental.is_fast_flatbuffers_builder_enabled()
    assert not experimental.is_flatbuffers_codegen_enabled()
    experimental.enable_fast_flatbuffers_builder()
    assert experimental.is_fast_flatbuffers_builder_enabled()
    assert not experimental._flatbuffers_verify
    experimental.enable_fast_flatbuffers_builder(False, verify=True)  # verify only applies when enabled
    assert not experimental.is_fast_flatbuffers_builder_enabled()
    assert not experimental._flatbuffers_verify


def test_switch_one_active(test_store, fast_builder_state):
    # Only one experimental builder is active: the last enabled one
    experimental.enable_fast_flatbuffers_builder(True, verify=True)
    experimental.enable_flatbuffers_codegen()
    assert experimental.is_flatbuffers_codegen_enabled()
    assert not experimental.is_fast_flatbuffers_builder_enabled()
    assert not experimental._flatbuffers_verify  # verify is set per enable call
    experimental.enable_fast_flatbuffers_builder(False)  # not active: no effect
    assert experimental.is_flatbuffers_codegen_enabled()
    experimental.enable_fast_flatbuffers_builder()
    assert experimental.is_fast_flatbuffers_builder_enabled()
    assert not experimental.is_flatbuffers_codegen_enabled()
    experimental.enable_flatbuffers_codegen(False)  # not active: no effect
    assert experimental.is_fast_flatbuffers_builder_enabled()
    experimental.enable_fast_flatbuffers_builder(False)
    assert experimental._flatbuffers_mode is None

    # The active one is used for marshalling
    obj = TestEntity(str="x")
    for mode in ENABLE:
        ENABLE[mode]()
        TestEntity._marshal(obj, 1)
    assert TestEntity._fast_builder is not None and TestEntity._codegen_builder is not None


@pytest.mark.parametrize("mode", ENABLE)
def test_verify_detects_differences(test_store, fast_builder_state, monkeypatch, mode):
    ENABLE[mode](True, verify=True)
    obj = TestEntity(str="x")
    assert TestEntity._marshal(obj, 1) == bytes(TestEntity._marshal_builder(obj, 1))
    builder = TestEntity._codegen_builder if mode == experimental.CODEGEN else TestEntity._fast_builder
    monkeypatch.setattr(builder, "marshal", lambda o, i: b"wrong")
    with pytest.raises(AssertionError, match="bytes differ"):
        TestEntity._marshal(obj, 1)


def test_codegen_source(test_store):
    """The generated source contains no values (they are passed via the namespace) and shows up in tracebacks."""
    builder = CodegenBuilder(TestEntity)
    assert builder.source.startswith("def marshal(obj, id):")
    assert "foo" not in builder.source and "1.5" not in builder.source
    assert linecache.getline(builder.filename, 1) == "def marshal(obj, id):\n"
    with pytest.raises(AttributeError) as error:
        builder.marshal(TestEntity(str=None), 1)
    assert any(entry.path == builder.filename and "encode" in str(entry.statement) for entry in error.traceback)
    assert CodegenBuilder(TestEntity).filename != builder.filename  # unique per builder


def test_codegen_entities_without_offset_properties(tmp_path):
    """No strings or vectors: the layout is fixed (residue 0) and selected when generating."""
    @Entity(model="fast-fb-scalars")
    class Scalars:
        id = Id
        a = Int32
        b = Int64

    model = Model()
    model.entity(Scalars)
    store = Store(model=model, directory=str(tmp_path / "db"), model_json_file=str(tmp_path / "model.json"))
    try:
        assert "_layout0" in CodegenBuilder(Scalars).source
        assert_same_bytes(Scalars, Scalars(a=-1, b=2 ** 40), id=7)
        assert_same_bytes(Scalars, Scalars())
    finally:
        store.close()
