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


import flatbuffers
import flatbuffers.flexbuffers
from typing import Generic
import numpy as np
from math import floor
from datetime import datetime
from objectbox.c import *
from objectbox.model.properties import Property
import threading

# _Entity class holds model information as well as conversions between python objects and FlatBuffers (ObjectBox data)
class _Entity(object):
    def __init__(self, cls, id: int, uid: int):
        # currently, ID and UID are mandatory and are not fetched from the model.json
        if id <= 0:
            raise Exception(
                "invalid or no 'id; given in the @Entity annotation")

        if uid <= 0:
            raise Exception(
                "invalid or no 'uid' given in the @Entity annotation")

        self.cls = cls
        self.name = cls.__name__
        self.id = id
        self.uid = uid

        self.last_property_id = None  # IdUid - set in model.entity()

        self.properties = list()  # List[Property]
        self.offset_properties = list()  # List[Property]
        self.id_property = None
        self.fill_properties()
        self._tl = threading.local()
        
    def __call__(self, **properties):
        """ The constructor of the user Entity class. """
        object_ = self.cls()
        for prop_name, prop_val in properties.items():
            if not hasattr(object_, prop_name):
                raise Exception(f"Entity {self.name} has no property \"{prop_name}\"")
            setattr(object_, prop_name, prop_val)
        return object_

    def fill_properties(self):
        # TODO allow subclassing and support entities with __slots__ defined
        variables = dict(vars(self.cls))

        # filter only subclasses of Property
        variables = {k: v for k, v in variables.items(
        ) if issubclass(type(v), Property)}

        for k, prop in variables.items():
            prop._name = k
            self.properties.append(prop)

            if prop._is_id:
                if self.id_property:
                    raise Exception("duplicate ID property: '%s' and '%s'" % (
                        self.id_property._name, prop._name))
                self.id_property = prop

            if prop._fb_type == flatbuffers.number_types.UOffsetTFlags:
                assert prop._ob_type in [
                    OBXPropertyType_String,
                    OBXPropertyType_BoolVector,
                    OBXPropertyType_ByteVector,
                    OBXPropertyType_ShortVector,
                    OBXPropertyType_CharVector,
                    OBXPropertyType_IntVector,
                    OBXPropertyType_LongVector,
                    OBXPropertyType_FloatVector,
                    OBXPropertyType_DoubleVector,
                    OBXPropertyType_Flex,
                ], "programming error - invalid type OB & FB type combination"
                self.offset_properties.append(prop)

            # print('Property {}.{}: {} (ob:{} fb:{})'.format(self.name, prop._name, prop._py_type, prop._ob_type, prop._fb_type))

        if not self.id_property:
            raise Exception("ID property is not defined")
        elif self.id_property._ob_type != OBXPropertyType_Long:
            raise Exception("ID property must be an int")

    def get_property(self, name: str):
        """ Gets the property having the given name. """
        for prop in self.properties:
            if prop._name == name:
                return prop
        raise Exception(f"Property \"{name}\" not found in Entity: \"{self.name}\"")

    def get_property_id(self, prop: Union[int, str, Property]) -> int:
        """ A convenient way to get the property ID regardless having its ID, name or Property. """
        if isinstance(prop, int):
            return prop  # We already have it!
        elif isinstance(prop, str):
            return self.get_property(prop)._id
        elif isinstance(prop, Property):
            return prop._id
        else:
            raise Exception(f"Unsupported Property type: {type(prop)}")

    def get_value(self, object, prop: Property):
        # in case value is not overwritten on the object, it's the Property object itself (= as defined in the Class)
        val = getattr(object, prop._name)
        if prop._py_type == np.ndarray:
            if (val == np.array(prop)).all():
                return np.array([])
        elif val == prop:
            if prop._py_type == datetime:
                return datetime.fromtimestamp(0)
            if prop._ob_type == OBXPropertyType_Flex:
                return None
            else:
                return prop._py_type()  # default (empty) value for the given type
        return val

    def get_object_id(self, object) -> int:
        return self.get_value(object, self.id_property)

    def set_object_id(self, object, id: int):
        setattr(object, self.id_property._name, id)

    def marshal(self, object, id: int) -> bytearray:
        if not hasattr(self._tl, "builder"):
            self._tl.builder = flatbuffers.Builder(256)
        builder = self._tl.builder
        builder.Clear()

        # prepare some properties that need to be built in FB before starting the main object
        offsets = {}
        for prop in self.offset_properties:
            val = self.get_value(object, prop)
            if prop._ob_type == OBXPropertyType_String:
                offsets[prop._id] = builder.CreateString(val.encode('utf-8'))
            elif prop._ob_type == OBXPropertyType_BoolVector:
                # Using a numpy bool as it seems to be more consistent in terms of size. TBD
                # https://numpy.org/doc/stable/reference/arrays.scalars.html#numpy.bool
                offsets[prop._id] = builder.CreateNumpyVector(np.array(val, dtype=np.bool_))
            elif prop._ob_type == OBXPropertyType_ByteVector:
                offsets[prop._id] = builder.CreateByteVector(val)
            elif prop._ob_type == OBXPropertyType_ShortVector:
                offsets[prop._id] = builder.CreateNumpyVector(np.array(val, dtype=np.int16))
            elif prop._ob_type == OBXPropertyType_CharVector:
                offsets[prop._id] = builder.CreateNumpyVector(np.array(val, dtype=np.uint16))
            elif prop._ob_type == OBXPropertyType_IntVector:
                offsets[prop._id] = builder.CreateNumpyVector(np.array(val, dtype=np.int32))
            elif prop._ob_type == OBXPropertyType_LongVector:
                offsets[prop._id] = builder.CreateNumpyVector(np.array(val, dtype=np.int64))
            elif prop._ob_type == OBXPropertyType_FloatVector:
                offsets[prop._id] = builder.CreateNumpyVector(np.array(val, dtype=np.float32))
            elif prop._ob_type == OBXPropertyType_DoubleVector:
                offsets[prop._id] = builder.CreateNumpyVector(np.array(val, dtype=np.float64))
            elif prop._ob_type == OBXPropertyType_Flex:
                flex_builder = flatbuffers.flexbuffers.Builder()
                flex_builder.Add(val)
                buffer = flex_builder.Finish()
                offsets[prop._id] = builder.CreateByteVector(bytes(buffer))
            else:
                assert False, "programming error - invalid type OB & FB type combination"

        # start the FlatBuffers object with the largest number of properties that were ever present in the Entity
        builder.StartObject(self.last_property_id.id)

        # add properties to the FB object
        for prop in self.properties:
            if prop._id in offsets:
                val = offsets[prop._id]
                if val:
                    builder.PrependUOffsetTRelative(val)
            else:
                val = id if prop == self.id_property else self.get_value(object, prop)
                if prop._ob_type == OBXPropertyType_Date:
                    if prop._py_type == datetime:
                        val = val.timestamp() * 1000  # timestamp returns seconds, convert to milliseconds
                    val = floor(val)  # use floor to allow for float types
                elif prop._ob_type == OBXPropertyType_DateNano:
                    if prop._py_type == datetime:
                        val = val.timestamp() * 1000000000  # convert to nanoseconds
                    val = floor(val)  # use floor to allow for float types
                builder.Prepend(prop._fb_type, val)

            builder.Slot(prop._fb_slot)

        builder.Finish(builder.EndObject())
        return builder.Output()

    def unmarshal(self, data: bytes):
        pos = flatbuffers.encode.Get(flatbuffers.packer.uoffset, data, 0)
        table = flatbuffers.Table(data, pos)

        # initialize an empty object
        obj = self.cls()

        # fill it with the data read from FlatBuffers
        for prop in self.properties:
            o = table.Offset(prop._fb_v_offset)
            val = None
            if not o:
                val = prop._py_type()  # use default (empty) value if not present in the object
            elif prop._ob_type == OBXPropertyType_String:
                val = table.String(o + table.Pos).decode('utf-8')
            elif prop._ob_type == OBXPropertyType_BoolVector:
                val = table.GetVectorAsNumpy(flatbuffers.number_types.BoolFlags, o)
            elif prop._ob_type == OBXPropertyType_ByteVector:
                # access the FB byte vector information
                start = table.Vector(o)
                size = table.VectorLen(o)
                # slice the vector as a requested type
                val = prop._py_type(table.Bytes[start:start+size])
            elif prop._ob_type == OBXPropertyType_ShortVector:
                val = table.GetVectorAsNumpy(flatbuffers.number_types.Int16Flags, o)
            elif prop._ob_type == OBXPropertyType_CharVector:
                val = table.GetVectorAsNumpy(flatbuffers.number_types.Int16Flags, o)
            elif prop._ob_type == OBXPropertyType_Date and prop._py_type == datetime:
                table_val = table.Get(prop._fb_type, o + table.Pos)
                val = datetime.fromtimestamp(table_val/1000) if table_val != 0 else datetime.fromtimestamp(0)  # default timestamp
            elif prop._ob_type == OBXPropertyType_DateNano and prop._py_type == datetime:
                table_val = table.Get(prop._fb_type, o + table.Pos)
                val = datetime.fromtimestamp(table_val/1000000000) if table_val != 0 else datetime.fromtimestamp(0)  # default timestamp
            elif prop._ob_type == OBXPropertyType_IntVector:
                val = table.GetVectorAsNumpy(flatbuffers.number_types.Int32Flags, o)
            elif prop._ob_type == OBXPropertyType_LongVector:
                val = table.GetVectorAsNumpy(flatbuffers.number_types.Int64Flags, o)
            elif prop._ob_type == OBXPropertyType_FloatVector:
                val = table.GetVectorAsNumpy(flatbuffers.number_types.Float32Flags, o)
            elif prop._ob_type == OBXPropertyType_DoubleVector:
                val = table.GetVectorAsNumpy(flatbuffers.number_types.Float64Flags, o)
            elif prop._ob_type == OBXPropertyType_Flex:
                # access the FB byte vector information
                start = table.Vector(o)
                size = table.VectorLen(o)
                # slice the vector as bytes
                buf = table.Bytes[start:start+size]
                val = flatbuffers.flexbuffers.Loads(buf)
            else:
                val = table.Get(prop._fb_type, o + table.Pos)
            if prop._py_type == list:
                val = val.tolist()
            setattr(obj, prop._name, val)
        return obj


def Entity(id: int = 0, uid: int = 0) -> Callable[[Type], _Entity]:
    """ Entity decorator that wraps _Entity to allow @Entity(id=, uid=); i.e. no class arguments. """
    def wrapper(class_):
        return _Entity(class_, id, uid)
    return wrapper
