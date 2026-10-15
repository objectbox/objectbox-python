import os
import subprocess
import sys

import pytest

# numpy is imported only where needed: importing it may start BLAS threads (e.g. OpenBLAS: one per core) that
# busy-wait for a moment, slowing down short-lived processes. flatbuffers imports numpy (if available), so it is
# imported lazily, too. Checked in a new process, as the test process has imported both already.

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

_SCRIPT = """
import sys
from objectbox import *
import objectbox.experimental

def loaded():
    return sorted(m for m in ("numpy", "flatbuffers") if m in sys.modules)

result = {"import": loaded()}
mode = sys.argv[1]
if mode == "fast":
    objectbox.experimental.enable_fast_flatbuffers_builder()
elif mode == "codegen":
    objectbox.experimental.enable_flatbuffers_codegen()

@Entity()
class Scalars:
    id = Id
    name = String()
    count = Int64
    score = Float32
    flag = Bool
    created = Date(py_type=int)
    data = Bytes

result["entity"] = loaded()
store = Store(directory="memory:lazy-imports", model_json_file=sys.argv[2])
box = store.box(Scalars)
id = box.put(Scalars(name="foo", count=42, score=1.5, flag=True, created=1234, data=b"xyz"))
result["put"] = loaded()
obj = box.get(id)
assert (obj.name, obj.count, obj.score, obj.flag, obj.created, obj.data) == ("foo", 42, 1.5, True, 1234, b"xyz")
assert [o.name for o in box.query(Scalars.name.equals("foo")).build().find()] == ["foo"]
result["get"] = loaded()
store.close()
print(result)
"""


def _loaded_modules(mode, tmp_path) -> dict:
    output = subprocess.check_output([sys.executable, "-c", _SCRIPT, mode, str(tmp_path / "model.json")],
                                     cwd=_ROOT, text=True)
    return eval(output)


def test_import_loads_neither_numpy_nor_flatbuffers(tmp_path):
    result = _loaded_modules("default", tmp_path)
    assert result["import"] == []
    assert result["entity"] == []
    # The reference (default) marshalling uses flatbuffers, which imports numpy
    assert result["put"] == ["flatbuffers", "numpy"]


@pytest.mark.parametrize("mode", ["fast", "codegen"])
def test_experimental_flatbuffers_without_numpy(mode, tmp_path):
    result = _loaded_modules(mode, tmp_path)
    assert result["import"] == []
    assert result["entity"] == []
    assert result["put"] == []
    if mode == "codegen":
        assert result["get"] == []  # codegen also reads without flatbuffers
    else:
        assert result["get"] == ["flatbuffers", "numpy"]  # reads with flatbuffers.Table


def test_fb_formats_match_flatbuffers_flags():
    """The struct formats replacing flatbuffers.number_types (to avoid importing it) must match its flags."""
    import struct
    import flatbuffers.number_types
    from objectbox.model.properties import PropertyType, _fb_formats, Property
    offsets = {PropertyType.string, PropertyType.flex} | {t for t in PropertyType if t.name.endswith("Vector")}
    expected_flags = {
        PropertyType.bool: flatbuffers.number_types.BoolFlags,
        PropertyType.byte: flatbuffers.number_types.Int8Flags,
        PropertyType.short: flatbuffers.number_types.Int16Flags,
        PropertyType.char: flatbuffers.number_types.Int8Flags,
        PropertyType.int: flatbuffers.number_types.Int32Flags,
        PropertyType.long: flatbuffers.number_types.Int64Flags,
        PropertyType.float: flatbuffers.number_types.Float32Flags,
        PropertyType.double: flatbuffers.number_types.Float64Flags,
        PropertyType.date: flatbuffers.number_types.Int64Flags,
        PropertyType.dateNano: flatbuffers.number_types.Int64Flags,
    }
    expected_flags.update({t: flatbuffers.number_types.UOffsetTFlags for t in offsets})
    assert set(_fb_formats) == set(PropertyType) == set(expected_flags)
    for ob_type, flags in expected_flags.items():
        fb_format = _fb_formats[ob_type]
        assert flags.packer_type.format[-1] == fb_format, ob_type  # e.g. "<i" (bool: "?", no byte order)
        assert flags.bytewidth == struct.calcsize("<" + fb_format), ob_type
        prop = Property(int, type=ob_type)
        assert prop._fb_format == fb_format
        assert prop._fb_type is flags  # resolved lazily
        assert "_fb_type" in prop.__dict__  # then cached
