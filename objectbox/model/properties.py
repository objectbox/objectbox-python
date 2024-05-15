# Copyright 2019-2024 ObjectBox Ltd. All rights reserved.
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

from enum import IntEnum
import flatbuffers.number_types
import numpy as np
from dataclasses import dataclass

from objectbox.c import *
from objectbox.condition import PropertyQueryCondition, PropertyQueryConditionOp


class PropertyType(IntEnum):
    bool = OBXPropertyType_Bool
    byte = OBXPropertyType_Byte
    short = OBXPropertyType_Short
    char = OBXPropertyType_Char
    int = OBXPropertyType_Int
    long = OBXPropertyType_Long
    float = OBXPropertyType_Float
    double = OBXPropertyType_Double
    string = OBXPropertyType_String
    date = OBXPropertyType_Date
    dateNano = OBXPropertyType_DateNano
    flex = OBXPropertyType_Flex
    # relation = OBXPropertyType_Relation
    boolVector = OBXPropertyType_BoolVector
    byteVector = OBXPropertyType_ByteVector
    shortVector = OBXPropertyType_ShortVector
    charVector = OBXPropertyType_CharVector
    intVector = OBXPropertyType_IntVector
    longVector = OBXPropertyType_LongVector
    floatVector = OBXPropertyType_FloatVector
    doubleVector = OBXPropertyType_DoubleVector
    # stringVector = OBXPropertyType_StringVector


fb_type_map = {
    PropertyType.bool: flatbuffers.number_types.BoolFlags,
    PropertyType.byte: flatbuffers.number_types.Int8Flags,
    PropertyType.short: flatbuffers.number_types.Int16Flags,
    PropertyType.char: flatbuffers.number_types.Int8Flags,
    PropertyType.int: flatbuffers.number_types.Int32Flags,
    PropertyType.long: flatbuffers.number_types.Int64Flags,
    PropertyType.float: flatbuffers.number_types.Float32Flags,
    PropertyType.double: flatbuffers.number_types.Float64Flags,
    PropertyType.string: flatbuffers.number_types.UOffsetTFlags,
    PropertyType.date: flatbuffers.number_types.Int64Flags,
    PropertyType.dateNano: flatbuffers.number_types.Int64Flags,
    PropertyType.flex: flatbuffers.number_types.UOffsetTFlags,
    # PropertyType.relation: flatbuffers.number_types.Int64Flags,
    PropertyType.boolVector: flatbuffers.number_types.UOffsetTFlags,
    PropertyType.byteVector: flatbuffers.number_types.UOffsetTFlags,
    PropertyType.shortVector: flatbuffers.number_types.UOffsetTFlags,
    PropertyType.charVector: flatbuffers.number_types.UOffsetTFlags,
    PropertyType.intVector: flatbuffers.number_types.UOffsetTFlags,
    PropertyType.longVector: flatbuffers.number_types.UOffsetTFlags,
    PropertyType.floatVector: flatbuffers.number_types.UOffsetTFlags,
    PropertyType.doubleVector: flatbuffers.number_types.UOffsetTFlags,
    # PropertyType.stringVector: flatbuffers.number_types.UOffsetTFlags,
}


class IndexType(IntEnum):
    VALUE = OBXPropertyFlags_INDEXED
    HASH = OBXPropertyFlags_INDEX_HASH
    HASH64 = OBXPropertyFlags_INDEX_HASH64


@dataclass
class Index:
    id: int
    uid: int
    # TODO HNSW isn't a type but HASH and HASH64 are, remove type member and make HashIndex and Hash64Index classes?
    type: IndexType = IndexType.VALUE


class HnswFlags(IntEnum):
    NONE = 0
    DEBUG_LOGS = 1
    DEBUG_LOGS_DETAILED = 2
    VECTOR_CACHE_SIMD_PADDING_OFF = 4
    REPARATION_LIMIT_CANDIDATES = 8


class VectorDistanceType(IntEnum):
    UNKNOWN = OBXVectorDistanceType_UNKNOWN
    EUCLIDEAN = OBXVectorDistanceType_EUCLIDEAN
    COSINE = OBXVectorDistanceType_COSINE
    DOT_PRODUCT = OBXVectorDistanceType_DOT_PRODUCT
    DOT_PRODUCT_NON_NORMALIZED = OBXVectorDistanceType_DOT_PRODUCT_NON_NORMALIZED

VectorDistanceType.UNKNOWN.__doc__ = "Not a real type, just best practice (e.g. forward compatibility)"
VectorDistanceType.EUCLIDEAN.__doc__ = "The default; typically 'euclidean squared' internally."
VectorDistanceType.COSINE.__doc__ = """
Cosine similarity compares two vectors irrespective of their magnitude (compares the angle of two vectors).
Often used for document or semantic similarity.
Value range: 0.0 - 2.0 (0.0: same direction, 1.0: orthogonal, 2.0: opposite direction)
"""
VectorDistanceType.DOT_PRODUCT.__doc__ = """
For normalized vectors (vector length == 1.0), the dot product is equivalent to the cosine similarity.
Because of this, the dot product is often preferred as it performs better.
Value range (normalized vectors): 0.0 - 2.0 (0.0: same direction, 1.0: orthogonal, 2.0: opposite direction)
"""
VectorDistanceType.DOT_PRODUCT_NON_NORMALIZED.__doc__ = """
A custom dot product similarity measure that does not require the vectors to be normalized.
Note: this is no replacement for cosine similarity (like DotProduct for normalized vectors is).
The non-linear conversion provides a high precision over the entire float range (for the raw dot product).
The higher the dot product, the lower the distance is (the nearer the vectors are).
The more negative the dot product, the higher the distance is (the farther the vectors are).
Value range: 0.0 - 2.0 (nonlinear; 0.0: nearest, 1.0: orthogonal, 2.0: farthest)
"""

@dataclass
class HnswIndex:
    id: int
    uid: int
    dimensions: int
    neighbors_per_node: Optional[int] = None
    indexing_search_count: Optional[int] = None
    flags: HnswFlags = HnswFlags.NONE
    distance_type: VectorDistanceType = VectorDistanceType.EUCLIDEAN
    reparation_backlink_probability: Optional[float] = None
    vector_cache_hint_size_kb: Optional[float] = None


class Property:
    def __init__(self, pytype: Type, **kwargs):
        self._id = kwargs['id']
        self._uid = kwargs['uid']
        self._name = ""  # set in Entity.fill_properties()

        self._py_type = pytype
        self._ob_type = kwargs['type'] if 'type' in kwargs else self._determine_ob_type()
        self._fb_type = fb_type_map[self._ob_type]

        self._is_id = isinstance(self, Id)
        self._flags = 0

        # FlatBuffers marshalling information
        self._fb_slot = self._id - 1
        self._fb_v_offset = 4 + 2 * self._fb_slot

        self._index = kwargs.get('index', None)

        self._set_flags()

    def _determine_ob_type(self) -> OBXPropertyType:
        """ Tries to infer the OBX property type from the Python type. """
        ts = self._py_type
        if ts == str:
            return OBXPropertyType_String
        elif ts == int:
            return OBXPropertyType_Long
        elif ts == bytes:  # or ts == bytearray: might require further tests on read objects due to mutability
            return OBXPropertyType_ByteVector
        elif ts == list or ts == np.ndarray:
            return OBXPropertyType_DoubleVector
        elif ts == float:
            return OBXPropertyType_Double
        elif ts == bool:
            return OBXPropertyType_Bool
        else:
            raise Exception("unknown property type %s" % ts)

    def _set_flags(self):
        if self._is_id:
            self._flags |= OBXPropertyFlags_ID

        if self._index is not None:
            self._flags |= OBXPropertyFlags_INDEXED
            if isinstance(self._index, Index):  # Generic index
                self._flags |= self._index.type

    def equals(self, value, case_sensitive: bool = True) -> PropertyQueryCondition:
        args = {'value': value, 'case_sensitive': case_sensitive}
        return PropertyQueryCondition(self._id, PropertyQueryConditionOp.EQ, args)

    def not_equals(self, value, case_sensitive: bool = True) -> PropertyQueryCondition:
        args = {'value': value, 'case_sensitive': case_sensitive}
        return PropertyQueryCondition(self._id, PropertyQueryConditionOp.NOT_EQ, args)

    def contains(self, value: str, case_sensitive: bool = True) -> PropertyQueryCondition:
        args = {'value': value, 'case_sensitive': case_sensitive}
        return PropertyQueryCondition(self._id, PropertyQueryConditionOp.CONTAINS, args)

    def starts_with(self, value: str, case_sensitive: bool = True) -> PropertyQueryCondition:
        args = {'value': value, 'case_sensitive': case_sensitive}
        return PropertyQueryCondition(self._id, PropertyQueryConditionOp.STARTS_WITH, args)

    def ends_with(self, value: str, case_sensitive: bool = True) -> PropertyQueryCondition:
        args = {'value': value, 'case_sensitive': case_sensitive}
        return PropertyQueryCondition(self._id, PropertyQueryConditionOp.ENDS_WITH, args)

    def greater_than(self, value, case_sensitive: bool = True) -> PropertyQueryCondition:
        args = {'value': value, 'case_sensitive': case_sensitive}
        return PropertyQueryCondition(self._id, PropertyQueryConditionOp.GT, args)

    def greater_or_equal(self, value, case_sensitive: bool = True) -> PropertyQueryCondition:
        args = {'value': value, 'case_sensitive': case_sensitive}
        return PropertyQueryCondition(self._id, PropertyQueryConditionOp.GTE, args)

    def less_than(self, value, case_sensitive: bool = True) -> PropertyQueryCondition:
        args = {'value': value, 'case_sensitive': case_sensitive}
        return PropertyQueryCondition(self._id, PropertyQueryConditionOp.LT, args)

    def less_or_equal(self, value, case_sensitive: bool = True) -> PropertyQueryCondition:
        args = {'value': value, 'case_sensitive': case_sensitive}
        return PropertyQueryCondition(self._id, PropertyQueryConditionOp.LTE, args)

    def between(self, a, b) -> PropertyQueryCondition:
        args = {'a': a, 'b': b}
        return PropertyQueryCondition(self._id, PropertyQueryConditionOp.BETWEEN, args)

    def nearest_neighbor(self, query_vector, element_count: int) -> PropertyQueryCondition:
        args = {'query_vector': query_vector, 'element_count': element_count}
        return PropertyQueryCondition(self._id, PropertyQueryConditionOp.NEAREST_NEIGHBOR, args)

    def contains_key_value(self, key: str, value: str, case_sensitive: bool = True) -> PropertyQueryCondition:
        args = {'key': key, 'value': value, 'case_sensitive': case_sensitive}
        return PropertyQueryCondition(self._id, PropertyQueryConditionOp.CONTAINS_KEY_VALUE, args)


# ID property (primary key)
class Id(Property):
    def __init__(self, py_type: type = int, id: int = 0, uid: int = 0):
        super(Id, self).__init__(py_type, id=id, uid=uid)
