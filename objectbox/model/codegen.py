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

Generates Python source for a marshal function per entity and compiles it once (like dataclasses or attrs generate
__init__). The generated function does what FastBuilder.marshal does, but unrolled for the entity's properties: no
loops over property descriptions and no dispatch on property kinds. The layouts (see fast_builder) are shared with a
FastBuilder, so both produce the same bytes as the generic flatbuffers.Builder.

The generated source contains no values: defaults, properties, numpy dtypes etc. are passed via the namespace of
exec. It is registered in linecache, so tracebacks show the generated lines.
"""

import itertools
import keyword
import linecache

import flatbuffers.flexbuffers
import numpy as np

from objectbox.model.fast_builder import FastBuilder, _pads, _uint32, _STRING, _BYTES, _NUMPY, _FLEX, \
    _FIELD_SCALAR, _FIELD_OFFSET, _FIELD_ID, _FIELD_DATE, _FIELD_BOOL
from objectbox.utils import date_value_to_int

_counter = itertools.count(1)  # unique file names for linecache


class CodegenBuilder:
    """Marshals objects of one entity with generated code; created after the entity's IDs are synced."""

    def __init__(self, entity):
        fast_builder = FastBuilder(entity)
        self.source = _generate_source(fast_builder)
        self.filename = "<objectbox codegen %s #%d>" % (entity._name, next(_counter))
        namespace = _namespace(fast_builder)
        exec(compile(self.source, self.filename, "exec"), namespace)
        lines = self.source.splitlines(True)
        linecache.cache[self.filename] = (len(self.source), None, lines, self.filename)  # mtime None: kept
        # The generated function; thread-safe: all state is local (layouts are created lazily, see FastBuilder)
        self.marshal = namespace["marshal"]


def _namespace(fast_builder: FastBuilder) -> dict:
    namespace = {
        "_layouts": fast_builder._layouts,
        "_layout": fast_builder._layout,
        "_pads": _pads,
        "_uint32_pack": _uint32.pack,
        "_date_value_to_int": date_value_to_int,
        "_asarray": np.asarray,
        "_FlexBuilder": flatbuffers.flexbuffers.Builder,
        "_bytes": bytes,
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
            add("    d%d = v.encode('utf-8')" % i)
            add("    n = _len(d%d)" % i)
            add("    pad = -(off + n + 1) & 3")
            add("    z%d = _pads[pad + 1]" % i)
            add("    l%d = _uint32_pack(n)" % i)
            add("    off += pad + 1 + n + 4")
        elif kind == _NUMPY:
            add("    if v is _p%d: v = _d%d" % (i, i))
            add("    a = _asarray(v, dtype=_t%d)" % i)
            add("    if a.ndim > 1: raise TypeError('multidimensional-ndarray passed to CreateNumpyVector')")
            add("    if a.dtype.str[0] != '<': a = a.byteswap(inplace=False)")
            add("    d%d = a.tobytes(order='C')" % i)
            add("    n = _len(d%d)" % i)
            add("    pad = -(off + n) & 3")
            add("    off += pad")
            add("    pad_align = -(off + n) & %d" % (np.dtype(dtype).alignment - 1))
            add("    z%d = _pads[pad_align + pad]" % i)
            add("    l%d = _uint32_pack(a.size)" % i)
            add("    off += pad_align + n + 4")
        else:  # _BYTES, _FLEX
            if kind == _FLEX:
                add("    if v is _p%d: v = None" % i)
                add("    flex = _FlexBuilder()")
                add("    flex.Add(v)")
                add("    d%d = _bytes(flex.Finish())" % i)
            else:
                add("    if v is _p%d: v = _d%d" % (i, i))
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
                values.append("s%d" % j)
            elif kind == _FIELD_DATE:
                values.append("_date_value_to_int(0.0 if s%d is _fp%d else s%d, _fd%d)" % (j, j, j, j))
            else:  # _FIELD_BOOL
                assert kind == _FIELD_BOOL
                add("    if s%d is _fp%d: s%d = False" % (j, j, j))
                add("    elif not (False <= s%d <= True): raise TypeError('bad number %%s for type bool' %% _str(s%d))"
                    % (j, j))
                values.append("s%d" % j)

    parts = ["layout.prefix", "layout.fields.pack(%s)" % ", ".join(values)]
    for i in reversed(range(len(offset_props))):
        parts += ["l%d" % i, "d%d" % i, "z%d" % i]
    add("    return b''.join((%s,))" % ", ".join(parts))
    return "\n".join(lines) + "\n"
