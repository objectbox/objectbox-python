# Copyright 2019-2023 ObjectBox Ltd. All rights reserved.
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

from objectbox.condition import QueryCondition, _ConditionOp
from objectbox.c import *
import flatbuffers.number_types
import numpy as np


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
    value = OBXPropertyFlags_INDEXED
    hash = OBXPropertyFlags_INDEX_HASH
    hash64 = OBXPropertyFlags_INDEX_HASH64


class Property:
    def __init__(self, py_type: type, id: int, uid: int, type: PropertyType = None, index: bool = None, index_type: IndexType = None):
        self._id = id
        self._uid = uid
        self._name = ""  # set in Entity.fill_properties()

        self._py_type = py_type
        self._ob_type = type if type != None else self.__determine_ob_type()
        self._fb_type = fb_type_map[self._ob_type]

        self._is_id = isinstance(self, Id)
        self._flags = OBXPropertyFlags(0)
        self.__set_flags()

        # FlatBuffers marshalling information
        self._fb_slot = self._id - 1
        self._fb_v_offset = 4 + 2*self._fb_slot

        if index_type:
            if index == True or index == None:
                self._index = True
                self._index_type = index_type
            elif index == False:
                raise Exception(f"trying to set index type on property with id {self._id} while index is set to False")
        else:
            self._index = index if index != None else False
            if index:
                self._index_type = IndexType.value if self._py_type != str else IndexType.hash


    def __determine_ob_type(self) -> OBXPropertyType:
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

    def __set_flags(self):
        if self._is_id:
            self._flags = OBXPropertyFlags_ID

    def op(self, op: _ConditionOp, value, case_sensitive: bool = True) -> QueryCondition:
        return QueryCondition(self._id, op, value, case_sensitive)

    def equals(self, value, case_sensitive: bool = True) -> QueryCondition:
        return self.op(_ConditionOp.eq, value, case_sensitive)
        
    def not_equals(self, value, case_sensitive: bool = True) -> QueryCondition:
        return self.op(_ConditionOp.notEq, value, case_sensitive)
    
    def contains(self, value: str, case_sensitive: bool = True) -> QueryCondition:
        return self.op(_ConditionOp.contains, value, case_sensitive)
    
    def starts_with(self, value: str, case_sensitive: bool = True) -> QueryCondition:
        return self.op(_ConditionOp.startsWith, value, case_sensitive)
    
    def ends_with(self, value: str, case_sensitive: bool = True) -> QueryCondition:
        return self.op(_ConditionOp.endsWith, value, case_sensitive)
    
    def greater_than(self, value, case_sensitive: bool = True) -> QueryCondition:
        return self.op(_ConditionOp.gt, value, case_sensitive)
    
    def greater_or_equal(self, value, case_sensitive: bool = True) -> QueryCondition:
        return self.op(_ConditionOp.greaterOrEq, value, case_sensitive)
    
    def less_than(self, value, case_sensitive: bool = True) -> QueryCondition:
        return self.op(_ConditionOp.lt, value, case_sensitive)
    
    def less_or_equal(self, value, case_sensitive: bool = True) -> QueryCondition:
        return self.op(_ConditionOp.lessOrEq, value, case_sensitive)
    
    def between(self, value_a, value_b) -> QueryCondition:
        return QueryCondition(self._id, _ConditionOp.between, value_a, value_b)
    

# ID property (primary key)
class Id(Property):
    def __init__(self, py_type: type = int, id: int = 0, uid: int = 0):
        super(Id, self).__init__(py_type, id, uid)
