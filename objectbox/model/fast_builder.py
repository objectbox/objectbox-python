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

"""Experimental fast FlatBuffers builder for objects (see objectbox.experimental).

Produces the same bytes as _Entity._marshal_builder (the generic flatbuffers.Builder), but with the layout precomputed
once per entity: instead of ~60 Python calls per property, each object takes a few C-implemented calls (struct, join).

How the reference lays out an object (the Builder writes back to front; "off" counts the bytes written so far):
1. Strings and vectors (_offset_properties order); each is aligned relative to off (Builder.Prep).
2. The fields in _properties order, each aligned to its size; the vtable slot of a field is the off after it.
3. The offset to the vtable (soffset), then the vtable: size, object size, one entry per slot (trailing empty slots
   trimmed). The vtable is never shared: the Builder is cleared for each object.
4. Padding to "minalign" (the largest alignment used, fixed per entity), then the offset to the table (root).
So everything after step 1 depends only on off modulo 8 after step 1: at most 8 layouts per entity, built lazily.
In memory (front to back) this gives: root, padding, vtable, soffset, the fields in reverse order, the strings and
vectors in reverse order; each item is followed by its alignment padding.
"""

import struct

import flatbuffers.flexbuffers
import numpy as np

from objectbox.c import *
from objectbox.utils import date_value_to_int

_uint32 = struct.Struct('<I')

# How vectors are marshalled by the reference (numpy dtype per property type; byte vectors are bytes)
_numpy_dtypes = {
    OBXPropertyType_BoolVector: np.bool_,
    OBXPropertyType_ShortVector: np.int16,
    OBXPropertyType_CharVector: np.uint16,
    OBXPropertyType_IntVector: np.int32,
    OBXPropertyType_LongVector: np.int64,
    OBXPropertyType_FloatVector: np.float32,
    OBXPropertyType_DoubleVector: np.float64,
}

# Kinds of offset (variable size) properties and of fields
_STRING, _BYTES, _NUMPY, _FLEX = range(4)
_FIELD_SCALAR, _FIELD_OFFSET, _FIELD_ID, _FIELD_DATE, _FIELD_BOOL = range(5)

_pads = [b'\0' * n for n in range(16)]  # padding (zero bytes) by length


class _Layout:
    """Fixed part of an object (everything but strings and vectors) for one residue of off modulo 8."""
    __slots__ = ('prefix', 'fields', 'offset_adjust')

    def __init__(self, prefix: bytes, fields: struct.Struct, offset_adjust: list):
        self.prefix = prefix  # root, padding, vtable, soffset, padding: constant
        self.fields = fields  # the fields in memory order (reverse _properties order), incl. padding
        self.offset_adjust = offset_adjust  # per offset field (memory order): uoffset = off + adjust - var_off


class FastBuilder:
    """Marshals objects of one entity; created after the entity's IDs are synced (they define the slots).

    Open question: null values. Like the reference, this writes every field, so the layout is fixed per residue.
    If null values are supported (in the reference first), a null field is left out (vtable entry 0) and the layout
    depends on which fields are null, too. Caching a layout per null combination does not scale in general: with
    32 nullable properties there are 2^32 combinations (times 8 residues).
    Likely approach: cache the layouts for objects without nulls only (as now) and compute the layout per object
    if a value is null (_create_layout, extended to skip null fields). Measured with the current _create_layout
    (Python 3.12), this is still about 3x faster than the reference, e.g. 3.2 µs instead of 11.4 µs for an entity
    with 3 properties, as the reference's time goes mostly to writing value by value (~170 Python calls per object),
    not to computing the layout. If needed, a small, size-limited cache for frequent null combinations could follow;
    a fallback to the reference instead would make objects with nulls ~12x slower.
    """

    def __init__(self, entity):
        self._num_slots = entity._last_property_iduid.id
        minalign = 4  # the soffset (and every string or vector) is aligned to 4

        # Offset properties in creation order: (kind, name, property (= unset), default value, numpy dtype)
        offset_props = []
        for prop in entity._offset_properties:
            ob_type = prop._ob_type
            dtype = None
            if ob_type == OBXPropertyType_String:
                kind, default = _STRING, ''
            elif ob_type == OBXPropertyType_ByteVector:
                kind, default = _BYTES, prop._py_type()
            elif ob_type == OBXPropertyType_Flex:
                kind, default = _FLEX, None
            else:
                kind, dtype = _NUMPY, _numpy_dtypes[ob_type]
                default = np.array([]) if prop._py_type == np.ndarray else prop._py_type()
                minalign = max(minalign, np.dtype(dtype).alignment)
            offset_props.append((kind, prop.name, prop, default, dtype))
        self._offset_props = offset_props

        # Fields in _properties order (for the layout): (property, struct format char or None for an offset, width)
        # and in memory order (for marshalling): (kind, name, property (= unset), value for unset or other data)
        offset_index = {prop.name: i for i, (_, _, prop, _, _) in enumerate(offset_props)}
        self._fields = []
        fields_in_memory_order = []
        for prop in entity._properties:
            flags = prop._fb_type
            width = flags.bytewidth
            minalign = max(minalign, width)
            ob_type = prop._ob_type
            if prop.name in offset_index:
                self._fields.append((prop, None, 4))
                fields_in_memory_order.append((_FIELD_OFFSET, None, None, offset_index[prop.name]))
                continue
            self._fields.append((prop, flags.packer_type.format[-1], width))
            if prop is entity._id_property:
                fields_in_memory_order.append((_FIELD_ID, None, None, None))
            elif ob_type == OBXPropertyType_Date or ob_type == OBXPropertyType_DateNano:
                multiplier = 1000 if ob_type == OBXPropertyType_Date else 1000000000
                fields_in_memory_order.append((_FIELD_DATE, prop.name, prop, multiplier))
            elif ob_type == OBXPropertyType_Bool:
                fields_in_memory_order.append((_FIELD_BOOL, prop.name, prop, False))
            else:
                fields_in_memory_order.append((_FIELD_SCALAR, prop.name, prop, prop._py_type()))
        fields_in_memory_order.reverse()
        self._fields_in_memory_order = fields_in_memory_order
        self._minalign = minalign
        self._layouts = [None] * 8

    def _layout(self, residue: int) -> _Layout:
        # Thread-safe without a lock: concurrent first calls create equal layouts, one of them is kept
        layout = self._layouts[residue]
        if layout is None:
            layout = self._layouts[residue] = self._create_layout(residue)
        return layout

    def _create_layout(self, residue: int) -> _Layout:
        """Simulates the reference Builder from step 2 on (see module doc), starting at off = residue."""
        off = residue
        writes = []  # back to front: (struct format, offset field adjust or None)
        slots = [0] * self._num_slots
        for prop, fmt, width in self._fields:
            pad = -off & (width - 1)
            off += pad
            writes.append(('x' * pad, None))
            if fmt is None:  # uoffset = off (before placing) + 4 - var_off, with off relative to the real start
                writes.append(('I', off + 4 - residue))
            else:
                writes.append((fmt, None))
            off += width
            slots[prop._fb_slot] = off
        pad = -off & 3
        off += pad + 4
        object_offset = off
        num_slots = self._num_slots
        while num_slots > 0 and slots[num_slots - 1] == 0:
            num_slots -= 1
        vtable_size = (num_slots + 2) * 2
        vtable = [vtable_size, object_offset - residue] + [object_offset - s if s else 0 for s in slots[:num_slots]]
        off += vtable_size
        pad_finish = -(off + 4) & (self._minalign - 1)
        off += pad_finish
        root = off + 4 - object_offset

        # Memory order: reverse of the writes
        prefix = (_uint32.pack(root) + _pads[pad_finish] + struct.pack('<%dH' % len(vtable), *vtable) +
                  struct.pack('<i', vtable_size) + _pads[pad])
        fmt = '<'
        offset_adjust = []
        for f, adjust in reversed(writes):
            fmt += f
            if adjust is not None:
                offset_adjust.append(adjust)
        return _Layout(prefix, struct.Struct(fmt), offset_adjust)

    def marshal(self, obj, id: int) -> bytes:
        """Returns the FlatBuffer of the given object, with the given ID (same bytes as _Entity._marshal_builder).
        Thread-safe: all state is local; unlike the reference, this needs no thread-local builder."""
        uint32_pack = _uint32.pack
        pads = _pads

        # Step 1: strings and vectors, in creation order. The parts are collected back to front (each part's
        # padding, data, length) and reversed at the end, giving memory order.
        off = 0
        parts = []
        var_offs = []
        for kind, name, prop, default, dtype in self._offset_props:
            val = getattr(obj, name)
            if val is prop:
                val = default
            if kind == _STRING:
                data = val.encode('utf-8')
                n = len(data)
                pad = -(off + n + 1) & 3
                parts.append(pads[pad + 1])
                parts.append(data)
                parts.append(uint32_pack(n))
                off += pad + 1 + n + 4
            elif kind == _NUMPY:
                array = np.asarray(val, dtype=dtype)  # as np.array in the reference, but no copy if not needed
                if array.ndim > 1:
                    raise TypeError("multidimensional-ndarray passed to CreateNumpyVector")
                if array.dtype.str[0] != '<':
                    array = array.byteswap(inplace=False)
                data = array.tobytes(order='C')
                n = len(data)
                pad4 = -(off + n) & 3
                off += pad4
                pad_align = -(off + n) & (array.dtype.alignment - 1)
                parts.append(pads[pad_align + pad4])
                parts.append(data)
                parts.append(uint32_pack(array.size))
                off += pad_align + n + 4
            else:  # _BYTES, _FLEX
                if kind == _FLEX:
                    flex_builder = flatbuffers.flexbuffers.Builder()
                    flex_builder.Add(val)
                    data = bytes(flex_builder.Finish())
                elif not isinstance(val, bytes):
                    raise TypeError("non-byte vector passed to CreateByteVector")
                else:
                    data = val
                n = len(data)
                pad = -(off + n) & 3
                parts.append(pads[pad])
                parts.append(data)
                parts.append(uint32_pack(n))
                off += pad + n + 4
            var_offs.append(off)

        # Steps 2-4: the fields in memory order (reverse _properties order)
        layout = self._layout(off & 7)
        offset_adjust = layout.offset_adjust
        offset_field = 0
        values = []
        for kind, name, prop, data in self._fields_in_memory_order:
            if kind == _FIELD_SCALAR:
                val = getattr(obj, name)
                values.append(data if val is prop else val)
            elif kind == _FIELD_OFFSET:
                values.append(off + offset_adjust[offset_field] - var_offs[data])
                offset_field += 1
            elif kind == _FIELD_ID:
                values.append(id)
            elif kind == _FIELD_DATE:
                val = getattr(obj, name)
                values.append(date_value_to_int(0.0 if val is prop else val, data))
            else:  # _FIELD_BOOL
                val = getattr(obj, name)
                if val is prop:
                    val = False
                elif not (False <= val <= True):
                    raise TypeError("bad number %s for type bool" % str(val))  # as flatbuffers' enforce_number
                values.append(val)
        parts.append(layout.fields.pack(*values))
        parts.append(layout.prefix)
        parts.reverse()
        return b''.join(parts)
