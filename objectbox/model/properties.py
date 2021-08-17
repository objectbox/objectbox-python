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


from objectbox.c import *
import flatbuffers.number_types


# base property
class Property:
    def __init__(self, py_type: type, id: int, uid: int):
        self._id = id
        self._uid = uid
        self._name = ""  # set in Entity.fillProperties()

        self._fb_type = None  # flatbuffers.number_types
        self._py_type = py_type
        self._ob_type = OBXPropertyType(0)
        self.__set_basic_type()

        self._is_id = isinstance(self, Id)
        self._flags = OBXPropertyFlags(0)
        self.__set_flags()

        # FlatBuffers marshalling information
        self._fb_slot = self._id - 1
        self._fb_v_offset = 4 + 2*self._fb_slot

    def __set_basic_type(self) -> OBXPropertyType:
        ts = self._py_type
        if ts == str:
            self._ob_type = OBXPropertyType_String
            self._fb_type = flatbuffers.number_types.UOffsetTFlags
        elif ts == int:
            self._ob_type = OBXPropertyType_Long
            self._fb_type = flatbuffers.number_types.Int64Flags
        elif ts == bytes:  # or ts == bytearray: might require further tests on read objects due to mutability
            self._ob_type = OBXPropertyType_ByteVector
            self._fb_type = flatbuffers.number_types.UOffsetTFlags
        elif ts == float:
            self._ob_type = OBXPropertyType_Double
            self._fb_type = flatbuffers.number_types.Float64Flags
        elif ts == bool:
            self._ob_type = OBXPropertyType_Bool
            self._fb_type = flatbuffers.number_types.BoolFlags
        else:
            raise Exception("unknown property type %s" % ts)

    def __set_flags(self):
        if self._is_id:
            self._flags = OBXPropertyFlags_ID


# ID property (primary key)
class Id(Property):
    def __init__(self, py_type: type = int, id: int = 0, uid: int = 0):
        super(Id, self).__init__(py_type, id, uid)
