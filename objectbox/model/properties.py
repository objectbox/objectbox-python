# Copyright 2019-2021 ObjectBox Ltd. All rights reserved.
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

from objectbox.c import *
import flatbuffers.number_types


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
    # date = OBXPropertyType_Date
    # relation = OBXPropertyType_Relation
    byteVector = OBXPropertyType_ByteVector
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
    # PropertyType.date: flatbuffers.number_types.Int64Flags,
    # PropertyType.relation: flatbuffers.number_types.Int64Flags,
    PropertyType.byteVector: flatbuffers.number_types.UOffsetTFlags,
    # PropertyType.stringVector: flatbuffers.number_types.UOffsetTFlags,
}


class Property:
    def __init__(self, py_type: type, id: int, uid: int, type: PropertyType = None):
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

    def __determine_ob_type(self) -> OBXPropertyType:
        ts = self._py_type
        if ts == str:
            return OBXPropertyType_String
        elif ts == int:
            return OBXPropertyType_Long
        elif ts == bytes:  # or ts == bytearray: might require further tests on read objects due to mutability
            return OBXPropertyType_ByteVector
        elif ts == float:
            return OBXPropertyType_Double
        elif ts == bool:
            return OBXPropertyType_Bool
        else:
            raise Exception("unknown property type %s" % ts)

    def __set_flags(self):
        if self._is_id:
            self._flags = OBXPropertyFlags_ID


# ID property (primary key)
class Id(Property):
    def __init__(self, py_type: type = int, id: int = 0, uid: int = 0):
        super(Id, self).__init__(py_type, id, uid)
