# Copyright 2026 ObjectBox Ltd. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Experimental FlatBuffers codegen for objects (see objectbox.experimental).

Generates Python source for a marshal and an unmarshal function per entity and compiles them once (like dataclasses
or attrs generate __init__).
- marshal (put) does what FastBuilder.marshal does, but unrolled for the entity's properties: no loops over property
  descriptions and no dispatch on property kinds. The layouts (see fast_builder) are shared with a FastBuilder, so both
  produce the same bytes as the generic flatbuffers.Builder.
- unmarshal (get, query) does what _Entity._unmarshal_table does (via flatbuffers.Table), with the vtable read at
  once and one struct call per field. Like the reference, it reads any valid FlatBuffer of the entity (it follows the
  vtable; fields may be missing or in any order), and it returns the same values (incl. the reference's quirks).

The generated source contains no values: defaults, properties, numpy dtypes etc. are passed via the namespace of
exec. It is registered in linecache, so tracebacks show the generated lines.
Null values: the generated marshal checks each value for None; an object with a null value is marshalled by
FastBuilder.marshal_with_nulls (generic, layout per null combination; see FastBuilder), objects without nulls are
unaffected but for these checks. Reading is unchanged: a missing field reads as the default, as in the reference.
"""

import hashlib
import importlib.machinery
import itertools
import keyword
import linecache
import os
import struct
from array import array
import sys
from datetime import datetime, timezone

from objectbox.model.fast_builder import FastBuilder, _pads, _uint32, _STRING, _BYTES, _NUMPY, _FLEX, _INT8_LIST, \
    _FIELD_SCALAR, _FIELD_OFFSET, _FIELD_ID, _FIELD_DATE, _FIELD_BOOL
from objectbox import experimental
from objectbox.c import OBXPropertyType_String, OBXPropertyType_ByteVector, OBXPropertyType_Flex, \
    OBXPropertyType_BoolVector, OBXPropertyType_ShortVector, OBXPropertyType_CharVector, OBXPropertyType_IntVector, \
    OBXPropertyType_LongVector, OBXPropertyType_FloatVector, OBXPropertyType_DoubleVector, OBXPropertyType_Date, \
    OBXPropertyType_DateNano
from objectbox.utils import date_value_to_int

_counter = itertools.count(1)  # unique file names for linecache


class CodegenBuilder:
    """Marshals and unmarshals objects of one entity with generated code; created after the entity's IDs are synced.
    The generated functions are thread-safe: all state is local (layouts are created lazily, see FastBuilder).
    The sources are generated at creation; each function is compiled at its first use (attribute marshal or
    unmarshal), as compiling takes most of the time (e.g. ~1 ms per function for 38 properties): a process that
    only puts or only reads objects of an entity compiles only one."""

    def __init__(self, entity):
        fast_builder = FastBuilder(entity)
        self.source = _generate_source(fast_builder)
        self.filename = _register(self.source, entity, "marshal")
        self._marshal_namespace = _namespace(fast_builder)

        self.unmarshal_source, self._unmarshal_namespace = _generate_unmarshal(entity)
        self.unmarshal_filename = _register(self.unmarshal_source, entity, "unmarshal")
        self._entity_name = entity._name

    def __getattr__(self, name):
        # Only called if the attribute is not set yet: compiles the function and sets it on the instance.
        # Concurrent first calls may compile it twice; equal, so either is fine.
        if name == "marshal":
            source, filename, namespace = self.source, self.filename, self._marshal_namespace
        elif name == "unmarshal":
            source, filename, namespace = self.unmarshal_source, self.unmarshal_filename, self._unmarshal_namespace
        else:
            raise AttributeError("'%s' object has no attribute '%s'" % (type(self).__name__, name))
        namespace = dict(namespace)  # exec adds the function (and __builtins__)
        exec(_compile(source, filename, self._entity_name, name), namespace)
        function = namespace[name]
        setattr(self, name, function)
        return function


def _compile(source: str, filename: str, entity_name: str, kind: str):
    """Compiles the source, or loads its compiled code from the cache directory (experimental._codegen_cache_dir):
    the source is written there as a .py file (named by its hash), which Python compiles and caches as usual
    (__pycache__ or sys.pycache_prefix, validated against the source).
    Any problem with the cache: compiles without it."""
    cache_dir = experimental._codegen_cache_dir
    if cache_dir is not None:
        try:
            return _compile_cached(source, cache_dir, entity_name, kind)
        except Exception:
            pass
    return compile(source, filename, "exec")


def _compile_cached(source: str, cache_dir: str, entity_name: str, kind: str):
    data = source.encode("utf-8")
    name = "objectbox_codegen_%s_%s_%s" % (kind, entity_name, hashlib.sha256(data).hexdigest()[:24])
    path = os.path.join(cache_dir, name + ".py")
    try:
        with open(path, "rb") as file:
            matches = file.read() == data
    except FileNotFoundError:
        matches = False
    if not matches:  # new (or e.g. damaged): write atomically, also if processes race
        os.makedirs(cache_dir, exist_ok=True)
        temp_path = "%s.%d.%s.tmp" % (path, os.getpid(), os.urandom(4).hex())
        try:
            with open(temp_path, "wb") as file:
                file.write(data)
            os.replace(temp_path, path)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
    return importlib.machinery.SourceFileLoader(name, path).get_code(name)


def _register(source: str, entity, kind: str) -> str:
    """Registers the source in linecache under a unique file name, so tracebacks show the generated lines."""
    filename = "<objectbox codegen %s %s #%d>" % (kind, entity._name, next(_counter))
    linecache.cache[filename] = (len(source), None, source.splitlines(True), filename)  # mtime None: kept
    return filename


def _namespace(fast_builder: FastBuilder) -> dict:
    namespace = {
        "_layouts": fast_builder._layouts,
        "_layout": fast_builder._layout,
        "_marshal_with_nulls": fast_builder.marshal_with_nulls,  # objects with null values: generic, slower
        "_pads": _pads,
        "_uint32_pack": _uint32.pack,
        "_date_value_to_int": date_value_to_int,
        "_asarray": getattr(fast_builder._np, "asarray", None),  # numpy and flatbuffers only if needed
        "_FlexBuilder": fast_builder._flex_builder,
        "_bytes": bytes,
        "_array": array,
        "_isinstance": isinstance,
        "_getattr": getattr,
        "_str": str,
        "_len": len,
    }
    for i, (kind, name, prop, default, dtype) in enumerate(fast_builder._offset_props):
        namespace.update({"_n%d" % i: name, "_p%d" % i: prop, "_d%d" % i: default, "_t%d" % i: dtype})
    for j, (kind, name, prop, data) in enumerate(fast_builder._fields_in_memory_order):
        namespace.update({"_fn%d" % j: name, "_fp%d" % j: prop, "_fd%d" % j: data})
    if not fast_builder._offset_props:
        namespace["_layout0"] = fast_builder._layout(0)  # no strings or vectors: always residue 0
    return namespace


def _get(name: str, name_var: str) -> str:
    """Expression reading the attribute from obj; getattr for names that are no plain identifiers."""
    if name.isidentifier() and not keyword.iskeyword(name):
        return "obj." + name
    return "_getattr(obj, %s)" % name_var


def _generate_source(fast_builder: FastBuilder) -> str:
    """Source of marshal(obj, id); mirrors FastBuilder.marshal step by step (see there)."""
    lines = ["def marshal(obj, id):"]
    add = lines.append
    offset_props = fast_builder._offset_props

    # Step 1: strings and vectors, in creation order; per property: data d<i>, its length l<i> and padding z<i>, and
    # its offset o<i> (bytes written so far after it)
    if offset_props:
        add("    off = 0")
    for i, (kind, name, prop, default, dtype) in enumerate(offset_props):
        add("    v = " + _get(name, "_n%d" % i))
        if kind == _STRING:
            add("    if v is _p%d: v = ''" % i)
            add("    elif v is None: return _marshal_with_nulls(obj, id)")
            add("    d%d = v.encode('utf-8')" % i)
            add("    n = _len(d%d)" % i)
            add("    pad = -(off + n + 1) & 3")
            add("    z%d = _pads[pad + 1]" % i)
            add("    l%d = _uint32_pack(n)" % i)
            add("    off += pad + 1 + n + 4")
        elif kind == _NUMPY:
            add("    if v is _p%d: v = _d%d" % (i, i))
            add("    elif v is None: return _marshal_with_nulls(obj, id)")
            add("    a = _asarray(v, dtype=_t%d)" % i)
            add("    if a.ndim > 1: raise TypeError('multidimensional-ndarray passed to CreateNumpyVector')")
            add("    if a.dtype.str[0] != '<': a = a.byteswap(inplace=False)")
            add("    d%d = a.tobytes(order='C')" % i)
            add("    n = _len(d%d)" % i)
            add("    pad = -(off + n) & 3")
            add("    off += pad")
            add("    pad_align = -(off + n) & %d" % (dtype.alignment - 1))
            add("    z%d = _pads[pad_align + pad]" % i)
            add("    l%d = _uint32_pack(a.size)" % i)
            add("    off += pad_align + n + 4")
        else:  # _BYTES, _INT8_LIST, _FLEX
            if kind == _INT8_LIST:
                add("    if v is _p%d: v = _d%d" % (i, i))
                add("    elif v is None: return _marshal_with_nulls(obj, id)")
                add("    d%d = _array('b', v).tobytes()" % i)
            elif kind == _FLEX:
                add("    if v is _p%d: v = None" % i)
                add("    flex = _FlexBuilder()")
                add("    flex.Add(v)")
                add("    d%d = _bytes(flex.Finish())" % i)
            else:
                add("    if v is _p%d: v = _d%d" % (i, i))
                add("    elif v is None: return _marshal_with_nulls(obj, id)")
                add("    if not _isinstance(v, _bytes): raise TypeError('non-byte vector passed to CreateByteVector')")
                add("    d%d = v" % i)
            add("    n = _len(d%d)" % i)
            add("    pad = -(off + n) & 3")
            add("    z%d = _pads[pad]" % i)
            add("    l%d = _uint32_pack(n)" % i)
            add("    off += pad + n + 4")
        add("    o%d = off" % i)

    # Steps 2-4: the layout for the residue, then the fields in memory order
    if offset_props:
        add("    layout = _layouts[off & 7]")
        add("    if layout is None: layout = _layout(off & 7)")
        add("    adjust = layout.offset_adjust")
    else:
        add("    layout = _layout0")
    values = []
    offset_field = 0
    for j, (kind, name, prop, data) in enumerate(fast_builder._fields_in_memory_order):
        if kind == _FIELD_OFFSET:
            values.append("off + adjust[%d] - o%d" % (offset_field, data))
            offset_field += 1
        elif kind == _FIELD_ID:
            values.append("id")
        else:
            add("    s%d = %s" % (j, _get(name, "_fn%d" % j)))
            if kind == _FIELD_SCALAR:
                add("    if s%d is _fp%d: s%d = _fd%d" % (j, j, j, j))
                add("    elif s%d is None: return _marshal_with_nulls(obj, id)" % j)
                values.append("s%d" % j)
            elif kind == _FIELD_DATE:
                add("    if s%d is None: return _marshal_with_nulls(obj, id)" % j)
                values.append("_date_value_to_int(0.0 if s%d is _fp%d else s%d, _fd%d)" % (j, j, j, j))
            else:  # _FIELD_BOOL
                assert kind == _FIELD_BOOL
                add("    if s%d is _fp%d: s%d = False" % (j, j, j))
                add("    elif s%d is None: return _marshal_with_nulls(obj, id)" % j)
                add("    elif not (False <= s%d <= True): raise TypeError('bad number %%s for type bool' %% _str(s%d))"
                    % (j, j))
                values.append("s%d" % j)

    parts = ["layout.prefix", "layout.fields.pack(%s)" % ", ".join(values)]
    for i in reversed(range(len(offset_props))):
        parts += ["l%d" % i, "d%d" % i, "z%d" % i]
    add("    return b''.join((%s,))" % ", ".join(parts))
    return "\n".join(lines) + "\n"


# Reading: how _Entity._unmarshal_table reads each property type (via flatbuffers.Table)
_STRUCTS = {}  # struct format: unpack_from


def _unpack(fmt: str):
    unpack = _STRUCTS.get(fmt)
    if unpack is None:
        unpack = _STRUCTS[fmt] = struct.Struct(fmt).unpack_from
    return unpack


_numpy_read_dtypes = {  # as Table.GetVectorAsNumpy with these flatbuffers.number_types (note: chars as int16)
    OBXPropertyType_BoolVector: "bool",
    OBXPropertyType_ShortVector: "int16",
    OBXPropertyType_CharVector: "int16",
    OBXPropertyType_IntVector: "int32",
    OBXPropertyType_LongVector: "int64",
    OBXPropertyType_FloatVector: "float32",
    OBXPropertyType_DoubleVector: "float64",
}


def absent_value_factory(prop):
    """Callable without arguments returning the value read for a property missing from an object (written as null,
    or by an older model): its default, as an unset property is written. For most types, the type itself (e.g. str()
    gives ''); datetime, numpy arrays and Flex cannot be created that way."""
    ob_type = prop._ob_type
    if ob_type == OBXPropertyType_Flex:
        return lambda: None
    if prop._py_type == datetime:
        epoch = datetime.fromtimestamp(0, timezone.utc)
        return lambda: epoch  # immutable
    if prop._is_ndarray:
        import numpy as np  # imported already: numpy arrays are only read with numpy
        dtype = np.dtype(_numpy_read_dtypes[ob_type]).newbyteorder("<")
        return lambda: np.array([], dtype=dtype)
    return prop._py_type


def _set(name: str, name_var: str) -> str:
    """Statement prefix assigning the attribute on obj; setattr for names that are no plain identifiers."""
    if name.isidentifier() and not keyword.iskeyword(name):
        return "    obj.%s = " % name
    return "    _setattr(obj, %s, " % name_var


def _generate_unmarshal(entity):
    """Source and namespace of unmarshal(data); mirrors _Entity._unmarshal_table property by property."""
    namespace = {
        "_new": entity._user_type,
        "_u32": _unpack("<I"),
        "_s32": _unpack("<i"),
        "_u16": _unpack("<H"),
        "_fromtimestamp": datetime.fromtimestamp,
        "_utc": timezone.utc,
        "_setattr": setattr,
    }
    properties = entity._properties
    num_slots = max([prop._fb_slot for prop in properties] + [-1]) + 1
    namespace["_vtable"] = _unpack("<%dH" % num_slots)
    full_vtable_size = 4 + 2 * num_slots
    lines = [
        "def unmarshal(data):",
        "    pos = _u32(data, 0)[0]",
        "    vt = pos - _s32(data, pos)[0]",
        "    vt_size = _u16(data, vt)[0]",
        "    if vt_size >= %d:" % full_vtable_size,
        "        e = _vtable(data, vt + 4)",
        "    else:  # fewer fields in the vtable (e.g. written by an older model); missing ones read as 0 (= absent)",
        "        e = _vtable(data[:vt + vt_size] + b'\\0' * %d, vt + 4)" % (full_vtable_size - 4),
        "    obj = _new()",
    ]
    add = lines.append
    for k, prop in enumerate(properties):
        ob_type = prop._ob_type
        py_type = prop._py_type
        namespace["_n%d" % k] = prop.name
        namespace["_default%d" % k] = py_type
        namespace["_absent%d" % k] = absent_value_factory(prop)
        to_list = ".tolist()" if py_type == list else ""  # list types: read as numpy arrays
        add("    o = e[%d]" % prop._fb_slot)
        add("    if o:")
        if ob_type in (OBXPropertyType_String, OBXPropertyType_ByteVector, OBXPropertyType_Flex) or \
                ob_type in _numpy_read_dtypes:
            add("        p = pos + o")
            add("        p += _u32(data, p)[0]")
            add("        n = _u32(data, p)[0]")
            add("        p += 4")
            if ob_type == OBXPropertyType_String:
                add("        v = data[p:p + n].decode()")  # UTF-8 (the default; faster without the argument)
            elif ob_type == OBXPropertyType_ByteVector:
                if py_type == list:  # Int8List: signed bytes
                    namespace["_array"] = array
                    add("        v = _array('b', data[p:p + n]).tolist()")
                else:
                    add("        v = _default%d(data[p:p + n])" % k)
            elif ob_type == OBXPropertyType_Flex:
                import flatbuffers.flexbuffers  # imports numpy (if available), so only if needed
                namespace["_flex_loads"] = flatbuffers.flexbuffers.Loads
                add("        v = _flex_loads(data[p:p + n])")
            else:
                import numpy as np
                namespace["_frombuffer"] = np.frombuffer
                namespace["_dtype%d" % k] = np.dtype(_numpy_read_dtypes[ob_type]).newbyteorder("<")
                add("        v = _frombuffer(data, dtype=_dtype%d, count=n, offset=p)%s" % (k, to_list))
        else:
            namespace["_get%d" % k] = _unpack("<" + prop._fb_format)
            read = "_get%d(data, pos + o)[0]" % k
            if ob_type == OBXPropertyType_Date and py_type == datetime:
                read = "_fromtimestamp(%s / 1000.0, _utc)" % read  # tz positionally: faster
            elif ob_type == OBXPropertyType_Date and py_type == float:
                read = "%s / 1000.0" % read
            elif ob_type == OBXPropertyType_DateNano and py_type == datetime:
                read = "_fromtimestamp(%s / 1000000000.0, _utc)" % read
            add("        v = " + read)
        add("    else:")
        add("        v = _absent%d()  # default (empty) value if not present in the object" % k)
        assign = _set(prop.name, "_n%d" % k)
        add(assign + "v" + (")" if assign.startswith("    _setattr") else ""))
    add("    return obj")
    return "\n".join(lines) + "\n", namespace


def same_values(a, b) -> bool:
    """Whether two unmarshalled values are equal, incl. their types (numpy arrays: dtype and bytes; NaN equals NaN)."""
    if type(a) is not type(b):
        return False
    np = sys.modules.get("numpy")
    if np is not None and isinstance(a, np.ndarray):
        return a.dtype == b.dtype and a.shape == b.shape and a.tobytes() == b.tobytes()
    if isinstance(a, float):
        return a == b or (a != a and b != b)
    if isinstance(a, (list, tuple)):
        return len(a) == len(b) and all(same_values(x, y) for x, y in zip(a, b))
    if isinstance(a, dict):
        return a.keys() == b.keys() and all(same_values(a[key], b[key]) for key in a)
    return a == b
