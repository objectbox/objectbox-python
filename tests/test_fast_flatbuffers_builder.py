"""Experimental fast FlatBuffers builder and codegen: the bytes must equal those of the generic flatbuffers.Builder
(reference); objects read by the codegen must equal those read via flatbuffers.Table (reference)."""
import linecache
import math
import random
from datetime import datetime, timezone

import flatbuffers
import numpy as np
import pytest

from objectbox import experimental, Entity, Id, Int16, Int32, Int64, Float64, Date, Model, Store, String, \
    Float32Vector, Int64Vector, Bytes, Int8List, Float32List, Flex
from objectbox.model.codegen import CodegenBuilder, same_values
from objectbox.model.fast_builder import FastBuilder
from tests.common import create_test_store
from tests.model import TestEntity, TestEntityDatetime, TestEntityFlex, VectorEntity


@pytest.fixture
def fast_builder_state():
    """Restores the experimental switches (e.g. as set for the whole test suite) after a test that changes them."""
    saved = (experimental._flatbuffers_mode, experimental._flatbuffers_verify, experimental._codegen_cache_dir)
    yield
    experimental._flatbuffers_mode, experimental._flatbuffers_verify, experimental._codegen_cache_dir = saved


# The experimental switches per mode, e.g. for tests running with each builder
ENABLE = {
    experimental.FAST_BUILDER: experimental.enable_fast_flatbuffers_builder,
    experimental.CODEGEN: experimental.enable_flatbuffers_codegen,
}


def assert_same_bytes(entity, obj, id=1):
    """Checks both the fast builder and codegen against the reference, and reading the bytes back with codegen."""
    reference = bytes(entity._marshal_builder(obj, id))
    fast = FastBuilder(entity).marshal(obj, id)
    assert fast.hex() == reference.hex()  # hex: readable diff on failure
    codegen = CodegenBuilder(entity)
    generated = codegen.marshal(obj, id)
    assert generated.hex() == reference.hex()
    assert_same_read(entity, reference, codegen)
    return reference


def assert_same_read(entity, data, codegen=None):
    """Checks that codegen reads the same object as the reference (flatbuffers.Table)."""
    reference = entity._unmarshal_table(data)
    read = (codegen or CodegenBuilder(entity)).unmarshal(data)
    assert type(read) is type(reference)
    for prop in entity._properties:
        value, expected = getattr(read, prop.name), getattr(reference, prop.name)
        assert same_values(value, expected), f"{prop.name}: {value!r} != {expected!r}"
    return read


def complex_object(**overrides) -> TestEntity:
    """A TestEntity with all properties set (all property types)."""
    values = dict(str="foo bar", bool=True, int64=-1234567890123, int32=-123456, int16=-1234, int8=-12,
                  float64=1.2345678901, float32=1.5, bools=np.array([True, False, True]), bytes=b"\x00\x01\xff",
                  shorts=np.array([1, -2, 3]), chars=np.array([65, 66, 0xFFFF]), ints=np.array([1, -2, 3, 4, 5]),
                  longs=np.array([2 ** 40, -(2 ** 40)]), floats=np.array([1.5, -2.5]), doubles=np.array([0.1, 0.2]),
                  bools_list=[True, False], bytes_list=[-128, 0, 127], shorts_list=[-1, 2], chars_list=[0x41, 0x2603], ints_list=[1, 2, 3],
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


def store_for_entity(entity_class, tmp_path):
    model = Model()
    model.entity(entity_class)
    return Store(model=model, directory=str(tmp_path / "db"), model_json_file=str(tmp_path / "model.json"))


def test_codegen_read_foreign_layouts(tmp_path):
    """Codegen reads any valid FlatBuffer like the reference, not only the layout written by this binding:
    fields in another order, missing fields (vtable entry 0) and shorter vtables (e.g. written by an older model)."""
    @Entity(model="codegen-read")
    class Reading:
        id = Id
        text = String
        level = Int16
        score = Float64
        when = Date(int)
        values = Float32Vector

    store = store_for_entity(Reading, tmp_path)
    try:
        slot = {prop.name: prop._fb_slot for prop in Reading._properties}
        assert slot == {"id": 0, "text": 1, "level": 2, "score": 3, "when": 4, "values": 5}

        # Fields in reverse order and with a shared string; "score" missing
        builder = flatbuffers.Builder(0)
        text = builder.CreateString("hello")
        values = builder.CreateNumpyVector(np.array([0.5, -1.5], dtype=np.float32))
        builder.StartObject(6)
        builder.PrependUOffsetTRelativeSlot(slot["values"], values, 0)
        builder.PrependInt64Slot(slot["when"], 1700000000123, 0)
        builder.PrependInt16Slot(slot["level"], -3, 0)
        builder.PrependUOffsetTRelativeSlot(slot["text"], text, 0)
        builder.PrependUint64Slot(slot["id"], 42, 0)
        builder.Finish(builder.EndObject())
        read = assert_same_read(Reading, bytes(builder.Output()))
        assert (read.id, read.text, read.level, read.score, read.when) == (42, "hello", -3, 0.0, 1700000000123)
        assert read.values.tolist() == [0.5, -1.5]

        # Shorter vtable: only id and text (as written by a model without the other properties)
        builder = flatbuffers.Builder(0)
        text = builder.CreateString("old")
        builder.StartObject(2)
        builder.PrependUOffsetTRelativeSlot(slot["text"], text, 0)
        builder.PrependUint64Slot(slot["id"], 7, 0)
        builder.Finish(builder.EndObject())
        data = bytes(builder.Output())
        read = assert_same_read(Reading, data)  # the missing numpy vector: empty
        assert read.id == 7 and read.values.dtype == np.float32 and read.values.size == 0
    finally:
        store.close()


def test_codegen_read_older_model(tmp_path, fast_builder_state):
    """Objects written before properties were added are read with defaults for the new properties."""
    @Entity(model="codegen-read-v1")
    class Versioned:
        id = Id
        text = String

    store = store_for_entity(Versioned, tmp_path)
    store.box(Versioned).put(Versioned(text="v1"))
    store.close()

    @Entity(model="codegen-read-v2")
    class Versioned:
        id = Id
        text = String
        level = Int32
        name = String
        bytes_list = Int8List
        floats_list = Float32List
        created = Date(py_type=datetime)
        vector = Float32Vector
        flex = Flex

    store = store_for_entity(Versioned, tmp_path)
    try:
        experimental.enable_flatbuffers_codegen(True, verify=True)
        read = store.box(Versioned).get(1)
        assert (read.text, read.level, read.name, read.bytes_list, read.floats_list) == ("v1", 0, "", [], [])
        # Types whose default cannot be created by calling the type (failed to read before)
        assert read.created == datetime.fromtimestamp(0, timezone.utc)
        assert read.vector.dtype == np.float32 and read.vector.size == 0
        assert read.flex is None
        experimental._flatbuffers_mode = None  # the reference reads the same
        read = store.box(Versioned).get(1)
        assert read.created == datetime.fromtimestamp(0, timezone.utc) and read.vector.size == 0
    finally:
        store.close()


def test_codegen_read_errors_as_reference(tmp_path, fast_builder_state):
    """Data the reference cannot read: with codegen enabled, the reference's error is raised."""
    @Entity(model="codegen-read-errors")
    class Dated:
        id = Id
        text = String

    store = store_for_entity(Dated, tmp_path)
    try:
        builder = flatbuffers.Builder(0)
        text = builder.CreateString(b"\xff\xfe")  # invalid UTF-8
        builder.StartObject(2)
        builder.PrependUOffsetTRelativeSlot(1, text, 0)
        builder.PrependUint64Slot(0, 1, 0)
        builder.Finish(builder.EndObject())
        data = bytes(builder.Output())
        with pytest.raises(UnicodeDecodeError) as reference:
            Dated._unmarshal_table(data)
        experimental.enable_flatbuffers_codegen()
        with pytest.raises(reference.type):
            Dated._unmarshal(data)
        experimental.enable_flatbuffers_codegen(True, verify=True)
        with pytest.raises(reference.type):
            Dated._unmarshal(data)
    finally:
        store.close()


def test_codegen_read_used(test_store, fast_builder_state):
    """get, get_many, get_all and queries read with codegen when it is enabled (and only then)."""
    box = test_store.box(TestEntity)
    box.put([complex_object(str=f"o{i}", int32=i) for i in range(5)])
    calls = []
    experimental.enable_flatbuffers_codegen()
    TestEntity._marshal(TestEntity(), 1)  # creates the generated functions
    unmarshal = TestEntity._codegen_builder.unmarshal
    TestEntity._codegen_builder.unmarshal = lambda data: calls.append(1) or unmarshal(data)
    assert box.get(1).str == "o0"
    assert [o.str for o in box.get_many([2, 3])] == ["o1", "o2"]
    assert len(box.get_all()) == 5
    assert [o.int32 for o in box.query(TestEntity.int32.greater_than(2)).build().find()] == [3, 4]
    assert len(calls) == 10
    experimental.enable_flatbuffers_codegen(False)
    box.get(1)
    assert len(calls) == 10


def test_codegen_read_verify_detects_differences(test_store, fast_builder_state, monkeypatch):
    experimental.enable_flatbuffers_codegen(True, verify=True)
    box = test_store.box(TestEntity)
    box.put(complex_object())
    assert box.get(1).str == "foo bar"
    unmarshal = TestEntity._codegen_builder.unmarshal

    def wrong(data):
        obj = unmarshal(data)
        obj.doubles = obj.doubles.astype(np.float32)  # same values, other type
        return obj

    monkeypatch.setattr(TestEntity._codegen_builder, "unmarshal", wrong)
    with pytest.raises(AssertionError, match="doubles differs"):
        box.get(1)


def test_codegen_read_source(test_store):
    builder = CodegenBuilder(TestEntity)
    assert builder.unmarshal_source.startswith("def unmarshal(data):")
    assert linecache.getline(builder.unmarshal_filename, 1) == "def unmarshal(data):\n"
    assert builder.unmarshal_filename != builder.filename


def test_same_values():
    assert same_values(math.nan, math.nan) and same_values([1, [math.nan]], [1, [math.nan]])
    assert not same_values(1, 1.0) and not same_values(1, True) and not same_values([1], [2])
    assert same_values(np.array([1.5], np.float32), np.array([1.5], np.float32))
    assert not same_values(np.array([1.5], np.float32), np.array([1.5], np.float64))
    assert same_values({"a": [1]}, {"a": [1]}) and not same_values({"a": 1}, {"b": 1})


def test_codegen_compiles_on_first_use(test_store):
    """Each generated function is compiled at its first use, once."""
    builder = CodegenBuilder(TestEntity)
    assert "marshal" not in builder.__dict__ and "unmarshal" not in builder.__dict__
    data = builder.marshal(complex_object(), 1)
    assert "marshal" in builder.__dict__ and "unmarshal" not in builder.__dict__
    assert builder.marshal is builder.marshal
    assert builder.unmarshal(data).str == "foo bar"
    assert "unmarshal" in builder.__dict__
    with pytest.raises(AttributeError):
        builder.other


def test_codegen_cache(test_store, fast_builder_state, tmp_path):
    """With a cache directory, the generated sources are written there and compiled code is reused."""
    cache_dir = tmp_path / "codegen-cache"
    experimental.enable_flatbuffers_codegen(cache_dir=str(cache_dir))
    obj = complex_object()
    reference = bytes(TestEntity._marshal_builder(obj, 1))
    builder = CodegenBuilder(TestEntity)
    assert builder.marshal(obj, 1) == reference
    assert_same_read(TestEntity, reference, builder)
    sources = sorted(path.name for path in cache_dir.glob("*.py"))
    assert len(sources) == 2 and sources[0].startswith("objectbox_codegen_marshal_TestEntity_")
    assert len(list((cache_dir / "__pycache__").glob("*.pyc"))) == 2
    source_path = next(cache_dir.glob("objectbox_codegen_marshal_*.py"))
    assert source_path.read_text() == builder.source
    assert builder.marshal.__code__.co_filename == str(source_path)  # tracebacks show the cached file

    # Another builder (e.g. in another process) uses the cached code; the files are not rewritten
    mtime = source_path.stat().st_mtime_ns
    second = CodegenBuilder(TestEntity)
    assert second.marshal(obj, 1) == reference
    assert second.marshal.__code__.co_filename == str(source_path)
    assert source_path.stat().st_mtime_ns == mtime

    # A damaged source file is rewritten
    source_path.write_text("damaged")
    assert CodegenBuilder(TestEntity).marshal(obj, 1) == reference
    assert source_path.read_text() == builder.source

    # Off again (each call sets the directory): compiled without the cache
    experimental.enable_flatbuffers_codegen()
    assert not CodegenBuilder(TestEntity).marshal.__code__.co_filename.endswith(".py")


def test_codegen_cache_errors(test_store, fast_builder_state, tmp_path, monkeypatch):
    """Problems with the cache directory never fail: the code is compiled without the cache."""
    obj = complex_object()
    reference = bytes(TestEntity._marshal_builder(obj, 1))
    not_a_dir = tmp_path / "file"
    not_a_dir.write_text("")
    experimental.enable_flatbuffers_codegen(cache_dir=str(not_a_dir))
    assert CodegenBuilder(TestEntity).marshal(obj, 1) == reference

    def fail(*args):
        raise OSError("no space left")
    monkeypatch.setattr("os.replace", fail)
    cache_dir = tmp_path / "codegen-cache"
    experimental.enable_flatbuffers_codegen(cache_dir=str(cache_dir))
    builder = CodegenBuilder(TestEntity)
    assert builder.marshal(obj, 1) == reference
    assert not builder.marshal.__code__.co_filename.endswith(".py")
    assert list(cache_dir.iterdir()) == []  # no temporary files left
