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
from datetime import datetime
import sys
from dataclasses import dataclass

from objectbox.c import *
from objectbox.condition import PropertyQueryCondition, PropertyQueryConditionOp
from objectbox.model.iduid import IdUid

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
    relation = OBXPropertyType_Relation
    boolVector = OBXPropertyType_BoolVector
    byteVector = OBXPropertyType_ByteVector
    shortVector = OBXPropertyType_ShortVector
    charVector = OBXPropertyType_CharVector
    intVector = OBXPropertyType_IntVector
    longVector = OBXPropertyType_LongVector
    floatVector = OBXPropertyType_FloatVector
    doubleVector = OBXPropertyType_DoubleVector
    # stringVector = OBXPropertyType_StringVector


# FlatBuffers struct format per type (as the packer of the flatbuffers.number_types flags, see Property._fb_type);
# strings, vectors and flex are offsets ('I'). This avoids importing flatbuffers, which imports numpy, if available.
_fb_formats = {
    PropertyType.bool: '?',
    PropertyType.byte: 'b',
    PropertyType.short: 'h',
    PropertyType.char: 'b',
    PropertyType.int: 'i',
    PropertyType.long: 'q',
    PropertyType.float: 'f',
    PropertyType.double: 'd',
    PropertyType.string: 'I',
    PropertyType.date: 'q',
    PropertyType.dateNano: 'q',
    PropertyType.flex: 'I',
    PropertyType.relation: 'q',
    PropertyType.boolVector: 'I',
    PropertyType.byteVector: 'I',
    PropertyType.shortVector: 'I',
    PropertyType.charVector: 'I',
    PropertyType.intVector: 'I',
    PropertyType.longVector: 'I',
    PropertyType.floatVector: 'I',
    PropertyType.doubleVector: 'I',
    # PropertyType.stringVector: 'I',
}

# flatbuffers.number_types flags per struct format
_fb_flags_names = {'?': 'BoolFlags', 'b': 'Int8Flags', 'h': 'Int16Flags', 'i': 'Int32Flags', 'q': 'Int64Flags',
                   'f': 'Float32Flags', 'd': 'Float64Flags', 'I': 'UOffsetTFlags'}


def _ndarray() -> type:
    """numpy.ndarray; imports numpy, so only call it where numpy is needed (e.g. vector properties)."""
    import numpy
    return numpy.ndarray


class IndexType(IntEnum):
    VALUE = OBXPropertyFlags_INDEXED
    HASH = OBXPropertyFlags_INDEX_HASH
    HASH64 = OBXPropertyFlags_INDEX_HASH64


class Index:
    """Property Index"""

    # TODO HNSW isn't a `type` but HASH and HASH64 are, remove type member and make HashIndex and Hash64Index classes?

    def __init__(self, type: IndexType = IndexType.VALUE, uid: int = 0):
        self.type = type

        self.iduid = IdUid(0, uid)

    @property
    def id(self):
        """ Index Id """
        return self.iduid.id

    @property
    def uid(self):
        """ Index UId """
        return self.iduid.uid

    def has_uid(self):
        return self.iduid.uid != 0


class HnswFlags(IntEnum):
    """
    Vector-Search HNSW Index Flags
    """
    
    NONE = 0
    """
    
    """
    
    DEBUG_LOGS = 1
    """
    Enables debug logs.
    """
    
    DEBUG_LOGS_DETAILED = 2
    """
    Enables "high volume" debug logs, e.g. individual gets/puts.
    """
    
    VECTOR_CACHE_SIMD_PADDING_OFF = 4
    """
    Padding for SIMD is enabled by default, which uses more memory but may be faster. This flag turns it off.
    """
    
    REPARATION_LIMIT_CANDIDATES = 8
    """
    If the speed of removing nodes becomes a concern in your use case, you can speed it up by setting this flag.
    By default, repairing the graph after node removals creates more connections to improve the graph's quality.
    The extra costs for this are relatively low (e.g. vs. regular indexing), and thus the default is recommended.
    """

class VectorDistanceType(IntEnum):
    """
    Vector-search distance computation strategy type
    """
    
    UNKNOWN = OBXVectorDistanceType_UNKNOWN
    """
    Not a real type, just best practice (e.g. forward compatibility)
    """
    
    EUCLIDEAN = OBXVectorDistanceType_EUCLIDEAN
    """
    The default; typically 'euclidean squared' internally."
    """
    
    COSINE = OBXVectorDistanceType_COSINE
    """
    Cosine similarity compares two vectors irrespective of their magnitude (compares the angle of two vectors).
    Often used for document or semantic similarity.
    Value range: 0.0 - 2.0 (0.0: same direction, 1.0: orthogonal, 2.0: opposite direction)
    """
    
    DOT_PRODUCT = OBXVectorDistanceType_DOT_PRODUCT
    """
    For normalized vectors (vector length == 1.0), the dot product is equivalent to the cosine similarity.
    Because of this, the dot product is often preferred as it performs better.
    Value range (normalized vectors): 0.0 - 2.0 (0.0: same direction, 1.0: orthogonal, 2.0: opposite direction)
    """
    
    DOT_PRODUCT_NON_NORMALIZED = OBXVectorDistanceType_DOT_PRODUCT_NON_NORMALIZED
    """
    A custom dot product similarity measure that does not require the vectors to be normalized.
    Note: this is no replacement for cosine similarity (like DotProduct for normalized vectors is).
    The non-linear conversion provides a high precision over the entire float range (for the raw dot product).
    The higher the dot product, the lower the distance is (the nearer the vectors are).
    The more negative the dot product, the higher the distance is (the farther the vectors are).
    Value range: 0.0 - 2.0 (nonlinear; 0.0: nearest, 1.0: orthogonal, 2.0: farthest)
    """

class HnswIndex:
    """Vector-Search HNSW Property Index"""
    def __init__(self,
                 dimensions: int,
                 neighbors_per_node: Optional[int] = None,
                 indexing_search_count: Optional[int] = None,
                 flags: HnswFlags = HnswFlags.NONE,
                 distance_type: VectorDistanceType = VectorDistanceType.EUCLIDEAN,
                 reparation_backlink_probability: Optional[float] = None,
                 vector_cache_hint_size_kb: Optional[float] = None,
                 uid: int = 0):
        """
        :param dimensions:
            Vector dimensionality.
        :param neighbors_per_node:
            Maximum number of neighbors per node (aka "M").
            Higher number increases the graph connectivity which can lead to better results, but higher resources usage.
            If no value is set, a default value taken (currently 30).
            Try e.g. 16 for faster but less accurate results, or 64 for more accurate results.           
        :param indexing_search_count:
            Maximum number of neighbors searched while indexing (aka "efConstruction").
            If not set, internally default value is currently set to 100, which can change in future version.
            The default value serves as a starting point that can likely be optimized for specific datasets and use cases.
            The higher the value, the more accurate the search, but the longer the indexing will take. 
            If indexing time is not a major concern, a value of at least 200 is recommended to improve search quality.           blah.
        :param flags:
            Set flags.
        :param distance_type:
            Set distance strategy type.
        :param reparation_backlink_probability:
            When repairing the graph after a node was removed, this gives the probability of adding backlinks to the repaired
            neighbors. The default is 1.0 (aka "always") as this should be worth a bit of extra costs as it improves the graph's quality.
        :param vector_cache_hint_size_kb:
            Vector cache hint size. This is a non-binding hint of the maximum size of the vector cache in KB (default: 2097152 or 2 GB/GiB).   
        """
        self.dimensions = dimensions
        self.neighbors_per_node = neighbors_per_node
        self.indexing_search_count = indexing_search_count
        self.flags = flags
        self.distance_type = distance_type
        self.reparation_backlink_probability = reparation_backlink_probability
        self.vector_cache_hint_size_kb = vector_cache_hint_size_kb

        self.iduid = IdUid(0, uid)

    @property
    def id(self):
        """ Index Id """
        return self.iduid.id

    @property
    def uid(self):
        """ Index Uid """
        return self.iduid.uid

    def has_uid(self):
        """ Returns true if Uid is set. """
        return self.uid != 0


class Property:
    def __init__(self, pytype: Type, uid: int = 0, **kwargs):
        self.iduid = IdUid(0, uid)
        self.name = ""  # Python attribute name; set in Entity.fill_properties()
        self._db_name = ""  # Name in the database and model JSON (camelCase by default); set in Entity.fill_properties()
        self._entity = None  # The _Entity this property belongs to; set in Entity.fill_properties()
        self.index = kwargs.get('index', None)

        self._py_type = pytype
        self._is_ndarray = pytype is getattr(sys.modules.get('numpy'), 'ndarray', None)  # numpy imported if ndarray
        self._ob_type = kwargs['type'] if 'type' in kwargs else self._determine_ob_type()
        self._fb_format = _fb_formats[self._ob_type]  # struct format of the field (offsets: 'I')

        self._flags = 0
        self._set_flags()

        self._fb_slot = None
        self._fb_v_offset = None

    def __getattr__(self, name):
        # Only called if the attribute is not set: _fb_type is resolved on first use, then set on the instance.
        if name == '_fb_type' and '_fb_format' in self.__dict__:
            import flatbuffers.number_types  # imports numpy (if available), so only when needed
            self._fb_type = getattr(flatbuffers.number_types, _fb_flags_names[self.__dict__['_fb_format']])
            return self._fb_type
        raise AttributeError("'%s' object has no attribute '%s'" % (type(self).__name__, name))

    @property
    def id(self):
        """ Property Id """
        return self.iduid.id

    @property
    def uid(self):
        """ Property Uid """
        return self.iduid.uid

    def has_uid(self):
        """ Returns true if property has a valid Uid """
        return self.uid != 0

    def is_id(self) -> bool:
        """ Check if Property is an Id Property. """
        return isinstance(self, Id)

    def on_sync(self):
        """ Method called once ID/UID are synced with the model file. """
        assert self.iduid.is_assigned()
        self._fb_slot = self.id - 1
        self._fb_v_offset = 4 + 2 * self._fb_slot

    def _determine_ob_type(self) -> OBXPropertyType:
        """ Tries to infer the OBX property type from the Python type. """
        ts = self._py_type
        if ts == str:
            return OBXPropertyType_String
        elif ts == int:
            return OBXPropertyType_Long
        elif ts == bytes:  # or ts == bytearray: might require further tests on read objects due to mutability
            return OBXPropertyType_ByteVector
        elif ts == list or self._is_ndarray:
            return OBXPropertyType_DoubleVector
        elif ts == float:
            return OBXPropertyType_Double
        elif ts == bool:
            return OBXPropertyType_Bool
        else:
            raise Exception("unknown property type %s" % ts)

    def _set_flags(self):
        if self.is_id():
            self._flags |= OBXPropertyFlags_ID

        if self.index is not None:
            self._flags |= OBXPropertyFlags_INDEXED
            if isinstance(self.index, Index):  # Generic index
                self._flags |= self.index.type

    def is_null(self) -> PropertyQueryCondition:
        """ *Is null* condition to be passed to :func:`Box.query`: matches objects without a value for this property,
        i.e. it was put with None (unset properties are stored with their default value, not null) """
        self._assert_ids_assigned()
        return PropertyQueryCondition(self.id, PropertyQueryConditionOp.IS_NULL, {})

    def is_not_null(self) -> PropertyQueryCondition:
        """ *Is not null* condition to be passed to :func:`Box.query`: matches objects with a value for this property """
        self._assert_ids_assigned()
        return PropertyQueryCondition(self.id, PropertyQueryConditionOp.NOT_NULL, {})

    def _assert_ids_assigned(self):
        # Using assert(s) so they can be optionally disabled for performance
        assert self.iduid.is_assigned(), f"Property \"{self.name}\" ID not assigned"
        if self.index is not None:
            assert self.index.iduid.is_assigned(), f"Property \"{self.name}\" index ID not assigned"

class _NumericProperty(Property):
    """Common class for numeric conditions.
    Implicitly no support for equals/not_equals, see also _IntProperty below.
    """
    def __init__(self, py_type : Type, **kwargs):
        super(_NumericProperty, self).__init__(py_type, **kwargs)
    
    def greater_than(self, value) -> PropertyQueryCondition:
        """ *Greater-than* (``>``) condition to be passed to :func:`objectbox.Box.query` """
        self._assert_ids_assigned()
        args = {'value': value}
        return PropertyQueryCondition(self.id, PropertyQueryConditionOp.GT, args)

    def greater_or_equal(self, value) -> PropertyQueryCondition:
        """ *Greater-or-equal* (``>=``) condition to be passed to :func:`Box.query` """
        self._assert_ids_assigned()
        args = {'value': value}
        return PropertyQueryCondition(self.id, PropertyQueryConditionOp.GTE, args)

    def less_than(self, value) -> PropertyQueryCondition:
        """ *Less-than* (``<``) condition to be passed to :func:`Box.query` """
        self._assert_ids_assigned()
        args = {'value': value}
        return PropertyQueryCondition(self.id, PropertyQueryConditionOp.LT, args)

    def less_or_equal(self, value) -> PropertyQueryCondition:
        """ *Less-or-equal* (``<=``) condition to be passed to :func:`Box.query` """
        self._assert_ids_assigned()
        args = {'value': value}
        return PropertyQueryCondition(self.id, PropertyQueryConditionOp.LTE, args)

    def between(self, a, b) -> PropertyQueryCondition:
        """ *Between* a and b (``a <= x <= b``) condition to be passed to :func:`Box.query` """
        self._assert_ids_assigned()
        args = {'a': a, 'b': b}
        return PropertyQueryCondition(self.id, PropertyQueryConditionOp.BETWEEN, args)

class _IntProperty(_NumericProperty):
    """Integer-based conditions.
    Adds support for equals/not_equals.
    """
    def __init__(self, py_type : Type, **kwargs):
        super(_IntProperty, self).__init__(py_type, **kwargs)
        
    def equals(self, value) -> PropertyQueryCondition:
        """ *Equals* (``==``) condition to be passed to :func:`Box.query` """
        self._assert_ids_assigned()
        args = {'value': value}
        return PropertyQueryCondition(self.id, PropertyQueryConditionOp.EQ, args)

    def not_equals(self, value) -> PropertyQueryCondition:
        """ *Not equals* (``!=``) condition to be passed to :func:`Box.query` """
        self._assert_ids_assigned()
        args = {'value': value}
        return PropertyQueryCondition(self.id, PropertyQueryConditionOp.NOT_EQ, args)

    def one_of(self, values: List[int]) -> PropertyQueryCondition:
        """ *one of* (``in``) condition to be passed to :func:`Box.query`;
        matches if the property value equals any of the given values.
        Supported for 32-bit (Int32) and 64-bit (Int64, Id, Date, DateNano, Relation) integer properties;
        raises a ``TypeError`` for other properties (e.g. Int8, Int16, Bool). """
        self._assert_ids_assigned()
        self._assert_one_of_supported()
        args = {'values': values}
        return PropertyQueryCondition(self.id, PropertyQueryConditionOp.ONE_OF, args)

    def not_one_of(self, values: List[int]) -> PropertyQueryCondition:
        """ *not one of* (``not in``) condition to be passed to :func:`Box.query`;
        matches if the property value equals none of the given values.
        Supported for 32-bit (Int32) and 64-bit (Int64, Id, Date, DateNano, Relation) integer properties;
        raises a ``TypeError`` for other properties (e.g. Int8, Int16, Bool). """
        self._assert_ids_assigned()
        self._assert_one_of_supported()
        args = {'values': values}
        return PropertyQueryCondition(self.id, PropertyQueryConditionOp.NOT_ONE_OF, args)

    def _assert_one_of_supported(self):
        # The C API only supports 32-bit and 64-bit integers for "in" conditions
        if self._ob_type not in (PropertyType.int, PropertyType.long, PropertyType.date, PropertyType.dateNano,
                                 PropertyType.relation):
            raise TypeError(f"Property \"{self.name}\" of type {PropertyType(self._ob_type).name} "
                            f"does not support one_of()/not_one_of(); supported are 32-bit and 64-bit integers")


# ID property (primary key)
class Id(_IntProperty):
    """Id Property"""
    def __init__(self, id : int = 0, uid : int = 0, py_type: type = int):
        super(Id, self).__init__(py_type, id=id, uid=uid)

# Bool property
class Bool(_IntProperty):
    """Boolean Property"""
    def __init__(self, id : int = 0, uid : int = 0, **kwargs):
        super(Bool, self).__init__(bool, type=PropertyType.bool, id=id, uid=uid, **kwargs)

# String property with starts/ends_with
class String(Property):
    """String Property"""
    def __init__(self, id: int = 0, uid : int = 0, **kwargs):
        super(String, self).__init__(str, type=PropertyType.string, id=id, uid=uid, **kwargs)
        
    def starts_with(self, value: str, case_sensitive: bool = True) -> PropertyQueryCondition:
        """ *starts with* (string-prefix) condition (opt-in: case-sensitive) to be passed to :func:`Box.query` """
        self._assert_ids_assigned()
        args = {'value': value, 'case_sensitive': case_sensitive}
        return PropertyQueryCondition(self.id, PropertyQueryConditionOp.STARTS_WITH, args)

    def ends_with(self, value: str, case_sensitive: bool = True) -> PropertyQueryCondition:
        """ *ends with* (string-suffix) condition (opt-in: case-sensitive) to be passed to :func:`Box.query` """
        self._assert_ids_assigned()
        args = {'value': value, 'case_sensitive': case_sensitive}
        return PropertyQueryCondition(self.id, PropertyQueryConditionOp.ENDS_WITH, args)
    
    def equals(self, value, case_sensitive: bool = True) -> PropertyQueryCondition:
        """ *equals* (``==``) condition (opt-in: case-sensitive) to be passed to :func:`Box.query` """
        self._assert_ids_assigned()
        args = {'value': value, 'case_sensitive': case_sensitive}
        return PropertyQueryCondition(self.id, PropertyQueryConditionOp.EQ, args)

    def not_equals(self, value, case_sensitive: bool = True) -> PropertyQueryCondition:
        """ *not-equals* (``~=``) condition (opt-in: case-sensitive) to be passed to :func:`Box.query` """
        self._assert_ids_assigned()
        args = {'value': value, 'case_sensitive': case_sensitive}
        return PropertyQueryCondition(self.id, PropertyQueryConditionOp.NOT_EQ, args)
    
    def contains(self, value: str, case_sensitive: bool = True) -> PropertyQueryCondition:
        """ *contains string* condition (opt-in: case-sensitive) to be passed to :func:`Box.query` """
        self._assert_ids_assigned()
        args = {'value': value, 'case_sensitive': case_sensitive}
        return PropertyQueryCondition(self.id, PropertyQueryConditionOp.CONTAINS, args)
    
    def greater_than(self, value, case_sensitive: bool = True) -> PropertyQueryCondition:
        """ *greater-than* condition (opt-in: case-sensitive) to be passed to :func:`Box.query` """
        self._assert_ids_assigned()
        args = {'value': value, 'case_sensitive': case_sensitive}
        return PropertyQueryCondition(self.id, PropertyQueryConditionOp.GT, args)

    def greater_or_equal(self, value, case_sensitive: bool = True) -> PropertyQueryCondition:
        """ *greater-or-equal* condition (opt-in: case-sensitive) to be passed to :func:`Box.query` """
        self._assert_ids_assigned()
        args = {'value': value, 'case_sensitive': case_sensitive}
        return PropertyQueryCondition(self.id, PropertyQueryConditionOp.GTE, args)

    def less_than(self, value, case_sensitive: bool = True) -> PropertyQueryCondition:
        """ *less-than* condition (opt-in: case-sensitive) to be passed to :func:`Box.query` """
        self._assert_ids_assigned()
        args = {'value': value, 'case_sensitive': case_sensitive}
        return PropertyQueryCondition(self.id, PropertyQueryConditionOp.LT, args)

    def less_or_equal(self, value, case_sensitive: bool = True) -> PropertyQueryCondition:
        """ *less-or-equal* condition (opt-in: case-sensitive) to be passed to :func:`Box.query` """
        self._assert_ids_assigned()
        args = {'value': value, 'case_sensitive': case_sensitive}
        return PropertyQueryCondition(self.id, PropertyQueryConditionOp.LTE, args)

    def one_of(self, values: List[str], case_sensitive: bool = True) -> PropertyQueryCondition:
        """ *one of* (``in``) condition (opt-in: case-sensitive) to be passed to :func:`Box.query`;
        matches if the property value equals any of the given values. """
        self._assert_ids_assigned()
        args = {'values': values, 'case_sensitive': case_sensitive, 'string': True}
        return PropertyQueryCondition(self.id, PropertyQueryConditionOp.ONE_OF, args)
 
# Signed Integer Numeric Properties
class Int8(_IntProperty):
    """Integer 8-bit Property"""
    def __init__(self, id : int = 0, uid : int = 0, **kwargs):
        super(Int8, self).__init__(int, type=PropertyType.byte, id=id, uid=uid, **kwargs)
class Int16(_IntProperty):
    """Integer 16-bit Property"""
    def __init__(self, id : int = 0, uid : int = 0, **kwargs):
        super(Int16, self).__init__(int, type=PropertyType.short, id=id, uid=uid, **kwargs)
class Int32(_IntProperty):
    """Integer 32-bit Property"""
    def __init__(self, id : int = 0, uid : int = 0, **kwargs):
        super(Int32, self).__init__(int, type=PropertyType.int, id=id, uid=uid, **kwargs)
class Int64(_IntProperty):
    """Integer 64-bit Property"""
    def __init__(self, id : int = 0, uid : int = 0, **kwargs):
        super(Int64, self).__init__(int, type=PropertyType.long, id=id, uid=uid, **kwargs)


class Relation(_IntProperty):
    """To-one relation: the ID of an object of the target entity (an int; 0 for none), e.g.
    ``customer_id = Relation(Customer)``. Unlike an ``Int64``, ObjectBox knows the target: e.g. removing the target
    object resets the relation to 0. The relation is indexed (no index for 0).

    Name it like the relation with an ``_id`` suffix (e.g. ``customer_id`` for a customer): it is stored as
    ``customerId``, as a ``ToOne`` named ``customer`` in Java, Kotlin and Dart stores its target ID, so the model and
    data match theirs (e.g. for Sync).

    :param target: the target entity, i.e. the class decorated with ``@Entity()``, or its name, e.g. for a relation to
        the entity itself (``parent_id = Relation("Node")``) or to an entity defined later.
    """

    def __init__(self, target, id: int = 0, uid: int = 0):
        from objectbox.model.entity import _Entity
        if not isinstance(target, (_Entity, str)):
            raise TypeError(f"Relation target must be an entity (a class decorated with @Entity()) or an entity name, "
                            f"got {target!r}")
        super(Relation, self).__init__(int, type=PropertyType.relation, id=id, uid=uid, index=Index())
        self._flags |= OBXPropertyFlags_INDEX_PARTIAL_SKIP_ZERO
        self._target = target

    @property
    def _target_name(self) -> str:
        return self._target if isinstance(self._target, str) else self._target._name


class SyncClock(Int64):
    """Sync clock property (64-bit integer) of a Sync entity (see ``@SyncEntity()``): a "hybrid logical clock" to
    resolve Sync conflicts. These clock values allow "last write wins" conflict resolution.

    There can be only one sync clock per Sync entity type; which is also recommended for basic conflict resolution.
    For new objects, keep the value 0 (the default) to reserve "a slot" in the object data. ObjectBox Sync updates
    this property automatically on put operations.
    As a hybrid clock, it combines a wall clock with a logical counter to compensate for some clock skew effects.
    To get a timestamp from a value, see ``Sync.sync_clock_timestamp()``.
    """
    def __init__(self, id : int = 0, uid : int = 0):
        super(SyncClock, self).__init__(id=id, uid=uid)
        self._flags |= OBXPropertyFlags_SYNC_CLOCK


class SyncPrecedence(Int64):
    """Sync precedence property (64-bit integer) of a Sync entity (see ``@SyncEntity()``) to customize Sync conflict
    resolution: developer-assigned precedence values are then used to resolve conflicts via "higher precedence wins".
    Defining and assigning precedence values are completely in the hands of the developer.

    There can be only one sync precedence per Sync entity type.
    Typically, it is combined with a ``SyncClock``, with the latter being the tie-breaker for equal precedence values.
    """
    def __init__(self, id : int = 0, uid : int = 0):
        super(SyncPrecedence, self).__init__(id=id, uid=uid)
        self._flags |= OBXPropertyFlags_SYNC_PRECEDENCE
        
# Floating-Point Numeric Properties
class Float32(_NumericProperty):
    """Floating-point 32-bit Property"""
    def __init__(self, id : int = 0, uid : int = 0, **kwargs):
        super(Float32, self).__init__(float, type=PropertyType.float, id=id, uid=uid, **kwargs)

class Float64(_NumericProperty):
    """Floating-point 64-bit Property"""
    def __init__(self, id : int = 0, uid : int = 0, **kwargs):
        super(Float64, self).__init__(float, type=PropertyType.double, id=id, uid=uid, **kwargs)

# Date Properties
class Date(_IntProperty):
    """Date Property"""
    def __init__(self, py_type = datetime, id : int = 0, uid : int = 0, **kwargs):
        super(Date, self).__init__(py_type, type=PropertyType.date, id=id, uid=uid, **kwargs)

class DateNano(_IntProperty):
    """Date (nano-second resolution) Property"""
    def __init__(self, py_type = datetime, id : int = 0, uid : int = 0, **kwargs):
        super(DateNano, self).__init__(py_type, type=PropertyType.dateNano, id=id, uid=uid, **kwargs)

# Bytes Property
class Bytes(_NumericProperty):
    """Bytes blob Property"""
    def __init__(self, id: int = 0, uid : int = 0, **kwargs):
        super(Bytes, self).__init__(bytes, type=PropertyType.byteVector, id=id, uid=uid, **kwargs)
    
    def equals(self, value) -> PropertyQueryCondition:
        """ *byte-string equals* (``==``) condition to be passed to :func:`Box.query` """
        self._assert_ids_assigned()
        args = {'value': value}
        return PropertyQueryCondition(self.id, PropertyQueryConditionOp.EQ, args)
    
    def greater_than(self, value) -> PropertyQueryCondition:
        """ *byte-string greater-than* (``==``) condition to be passed to :func:`Box.query` """
        self._assert_ids_assigned()
        args = {'value': value}
        return PropertyQueryCondition(self.id, PropertyQueryConditionOp.GT, args)

    def greater_or_equal(self, value) -> PropertyQueryCondition:
        """ *byte-string greater-or-equal* (``>=``) condition to be passed to :func:`Box.query` """
        self._assert_ids_assigned()
        args = {'value': value}
        return PropertyQueryCondition(self.id, PropertyQueryConditionOp.GTE, args)

    def less_than(self, value) -> PropertyQueryCondition:
        """ *byte-string less-than* (``<``) condition to be passed to :func:`Box.query` """
        self._assert_ids_assigned()
        args = {'value': value}
        return PropertyQueryCondition(self.id, PropertyQueryConditionOp.LT, args)

    def less_or_equal(self, value) -> PropertyQueryCondition:
        """ *byte-string less-or-equal* (``<``) condition to be passed to :func:`Box.query` """
        self._assert_ids_assigned()
        args = {'value': value}
        return PropertyQueryCondition(self.id, PropertyQueryConditionOp.LTE, args)

# Flex Property
class Flex(Property):
    """Flex dictionary-compatible Property"""
    def __init__(self, id : int = 0, uid : int = 0, **kwargs):
        super(Flex, self).__init__(Generic, type=PropertyType.flex, id=id, uid=uid, **kwargs)
    def contains_key_value(self, key: str, value: str, case_sensitive: bool = True) -> PropertyQueryCondition:
        """ *contains key/valuel* condition to be passed to :func:`Box.query` """
        self._assert_ids_assigned()
        args = {'key': key, 'value': value, 'case_sensitive': case_sensitive}
        return PropertyQueryCondition(self.id, PropertyQueryConditionOp.CONTAINS_KEY_VALUE, args)

class _VectorProperty(Property):
    def __init__(self, py_type : Type, **kwargs):
        super(_VectorProperty, self).__init__(py_type, **kwargs)

class BoolVector(_VectorProperty):
    """Boolean Vector Property"""
    def __init__(self, id: int = 0, uid: int = 0, **kwargs):
        super(BoolVector, self).__init__(_ndarray(), type=PropertyType.boolVector, id=id, uid=uid, **kwargs)
class Int8Vector(_VectorProperty):
    """Integer 8-bit Vector Property"""
    def __init__(self, id: int = 0, uid: int = 0, **kwargs):
        super(Int8Vector, self).__init__(bytes, type=PropertyType.byteVector, id=id, uid=uid, **kwargs)

class Int16Vector(_VectorProperty):
    """Integer 16-bit Vector Property"""
    def __init__(self, id: int = 0, uid: int = 0, **kwargs):
        super(Int16Vector, self).__init__(_ndarray(), type=PropertyType.shortVector, id=id, uid=uid, **kwargs)

class CharVector(_VectorProperty):
    """Char 16-bit Vector Property"""
    def __init__(self, id: int = 0, uid: int = 0, **kwargs):
        super(CharVector, self).__init__(_ndarray(), type=PropertyType.charVector, id=id, uid=uid, **kwargs)
 
class Int32Vector(_VectorProperty):
    """Integer 32-bit Vector Property"""
    def __init__(self, id: int = 0, uid: int = 0, **kwargs):
        super(Int32Vector, self).__init__(_ndarray(), type=PropertyType.intVector, id=id, uid=uid, **kwargs)

class Int64Vector(_VectorProperty):
    """Integer 64-bit Vector Property"""
    def __init__(self, id: int = 0, uid: int = 0, **kwargs):
        super(Int64Vector, self).__init__(_ndarray(), type=PropertyType.longVector, id=id, uid=uid, **kwargs)

class Float32Vector(_VectorProperty):
    """Floating-point 32-bit Vector Property"""
    def __init__(self, id: int = 0, uid: int = 0, **kwargs):
        super(Float32Vector, self).__init__(_ndarray(), type=PropertyType.floatVector, id=id, uid=uid, **kwargs)
    def nearest_neighbor(self, query_vector, element_count: int) -> PropertyQueryCondition:
        self._assert_ids_assigned()
        args = {'query_vector': query_vector, 'element_count': element_count}
        return PropertyQueryCondition(self.id, PropertyQueryConditionOp.NEAREST_NEIGHBOR, args)

class Float64Vector(_VectorProperty):
    """Floating-point 64-bit Vector Property"""
    def __init__(self, id: int = 0, uid: int = 0, **kwargs):
        super(Float64Vector, self).__init__(_ndarray(), type=PropertyType.doubleVector, id=id, uid=uid, **kwargs)

class _ListProperty(Property):
    def __init__(self, **kwargs):
        super(_ListProperty, self).__init__(list, **kwargs)

class BoolList(_ListProperty):
    """Boolean List Property"""
    def __init__(self, id: int = 0, uid: int = 0, **kwargs):
        super(BoolList, self).__init__(type=PropertyType.boolVector, id=id, uid=uid, **kwargs)

class Int8List(_ListProperty):
    """Integer 8-bit List Property"""
    def __init__(self, id: int = 0, uid: int = 0, **kwargs):
        super(Int8List, self).__init__(type=PropertyType.byteVector, id=id, uid=uid, **kwargs)

class Int16List(_ListProperty):
    """Integer 16-bit List Property"""
    def __init__(self, id: int = 0, uid: int = 0, **kwargs):
        super(Int16List, self).__init__(type=PropertyType.shortVector, id=id, uid=uid, **kwargs)

class Int32List(_ListProperty):
    """Integer 32-bit List Property"""
    def __init__(self, id: int = 0, uid: int = 0, **kwargs):
        super(Int32List, self).__init__(type=PropertyType.intVector, id=id, uid=uid, **kwargs)

class Int64List(_ListProperty):
    """Integer 64-bit List Property"""
    def __init__(self, id: int = 0, uid: int = 0, **kwargs):
        super(Int64List, self).__init__(type=PropertyType.longVector, id=id, uid=uid, **kwargs)

class Float32List(_ListProperty):
    """Floating-point 32-bit List Property"""
    def __init__(self, id: int = 0, uid: int = 0, **kwargs):
        super(Float32List, self).__init__(type=PropertyType.floatVector, id=id, uid=uid, **kwargs)

class Float64List(_ListProperty):
    """Floating-point 64-bit List Property"""
    def __init__(self, id: int = 0, uid: int = 0, **kwargs):
        super(Float64List, self).__init__(type=PropertyType.doubleVector, id=id, uid=uid, **kwargs)

class CharList(_ListProperty):
    """Char 16-bit List Property"""
    def __init__(self, id: int = 0, uid: int = 0, **kwargs):
        super(CharList, self).__init__(type=PropertyType.charVector, id=id, uid=uid, **kwargs)
