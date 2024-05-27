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
import inspect

import flatbuffers
import flatbuffers.flexbuffers
import numpy as np
from datetime import datetime, timezone
import logging
from objectbox.c import *
from objectbox.model.iduid import IdUid
from objectbox.model.properties import Property
from objectbox.utils import date_value_to_int
import threading


# _Entity class holds model information as well as conversions between python objects and FlatBuffers (ObjectBox data)
class _Entity(object):
    def __init__(self, user_type, uid: int = 0):
        self._user_type = user_type
        self._iduid = IdUid(0, uid)
        self._name = user_type.__name__
        self._last_property_iduid = IdUid(0, 0)

        self._properties: List[Property] = list()  # List[Property]
        self._offset_properties = list()  # List[Property]
        self._id_property = None
        self._fill_properties()
        self._tl = threading.local()

    @property
    def _id(self) -> int:
        return self._iduid.id

    @property
    def _uid(self) -> int:
        return self._iduid.uid

    def _has_uid(self) -> bool:
        return self._iduid.uid != 0

    def _on_sync(self):
        """ Method called once ID/UID are synced with the model file. """
        assert self._iduid.is_assigned()
        for prop in self._properties:
            prop.on_sync()

    def __call__(self, **properties):
        """ The constructor of the user Entity class. """
        object_ = self._user_type()
        for prop_name, prop_val in properties.items():
            if not hasattr(object_, prop_name):
                raise Exception(f"Entity {self._name} has no property \"{prop_name}\"")
            setattr(object_, prop_name, prop_val)
        return object_

    def __getattr__(self, name):
        """ Overload to get properties via "<Entity>.<Prop>" notation. """
        for prop in self._properties:
            if prop.name == name:
                return prop
        return self.__getattribute__(name)     

    def _fill_properties(self):
        # TODO allow subclassing and support entities with __slots__ defined
        variables = dict(vars(self._user_type))

        # filter only subclasses of Property
        variables = {k: v for k, v in variables.items(
        ) if issubclass(type(v), Property)}

        for prop_name, prop in variables.items():
            prop.name = prop_name
            self._properties.append(prop)

            if prop.is_id():
                if self._id_property:
                    raise Exception(f"Duplicate ID property: \"{self._id_property.name}\" and \"{prop.name}\"")
                self._id_property = prop

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
                self._offset_properties.append(prop)

            # print('Property {}.{}: {} (ob:{} fb:{})'.format(self._name, prop.name, prop._py_type, prop._ob_type, prop._fb_type))

        if not self._id_property:
            raise Exception("ID property is not defined")
        elif self._id_property._ob_type != OBXPropertyType_Long:
            raise Exception("ID property must be an int")

    def _get_property(self, name: str):
        """ Gets the property having the given name. """
        for prop in self._properties:
            if prop.name == name:
                return prop
        raise Exception(f"Property \"{name}\" not found in Entity: \"{self._name}\"")

    def _get_property_id(self, prop: Union[int, str, Property]) -> int:
        """ A convenient way to get the property ID regardless having its ID, name or Property. """
        if isinstance(prop, int):
            return prop  # We already have it!
        elif isinstance(prop, str):
            return self._get_property(prop).id
        elif isinstance(prop, Property):
            return prop.id
        else:
            raise Exception(f"Unsupported Property type: {type(prop)}")

    def _get_value(self, object, prop: Property):
        # in case value is not overwritten on the object, it's the Property object itself (= as defined in the Class)
        val = getattr(object, prop.name)
        if prop._py_type == np.ndarray:
            if (val == np.array(prop)).all():
                return np.array([])
        elif val == prop:
            if prop._ob_type == OBXPropertyType_Date or prop._ob_type == OBXPropertyType_DateNano:
                return 0.0  # For marshalling, prefer float over datetime
            elif prop._ob_type == OBXPropertyType_Flex:
                return None
            else:
                return prop._py_type()  # default (empty) value for the given type
        return val

    def _get_object_id(self, obj) -> int:
        return self._get_value(obj, self._id_property)

    def _set_object_id(self, obj, id_: int):
        setattr(obj, self._id_property.name, id_)

    def _marshal(self, object, id: int) -> bytearray:
        if not hasattr(self._tl, "builder"):
            self._tl.builder = flatbuffers.Builder(256)
        builder = self._tl.builder
        builder.Clear()

        # prepare some properties that need to be built in FB before starting the main object
        offsets = {}
        for prop in self._offset_properties:
            val = self._get_value(object, prop)
            if prop._ob_type == OBXPropertyType_String:
                offsets[prop.id] = builder.CreateString(val.encode('utf-8'))
            elif prop._ob_type == OBXPropertyType_BoolVector:
                # Using a numpy bool as it seems to be more consistent in terms of size. TBD
                # https://numpy.org/doc/stable/reference/arrays.scalars.html#numpy.bool
                offsets[prop.id] = builder.CreateNumpyVector(np.array(val, dtype=np.bool_))
            elif prop._ob_type == OBXPropertyType_ByteVector:
                offsets[prop.id] = builder.CreateByteVector(val)
            elif prop._ob_type == OBXPropertyType_ShortVector:
                offsets[prop.id] = builder.CreateNumpyVector(np.array(val, dtype=np.int16))
            elif prop._ob_type == OBXPropertyType_CharVector:
                offsets[prop.id] = builder.CreateNumpyVector(np.array(val, dtype=np.uint16))
            elif prop._ob_type == OBXPropertyType_IntVector:
                offsets[prop.id] = builder.CreateNumpyVector(np.array(val, dtype=np.int32))
            elif prop._ob_type == OBXPropertyType_LongVector:
                offsets[prop.id] = builder.CreateNumpyVector(np.array(val, dtype=np.int64))
            elif prop._ob_type == OBXPropertyType_FloatVector:
                offsets[prop.id] = builder.CreateNumpyVector(np.array(val, dtype=np.float32))
            elif prop._ob_type == OBXPropertyType_DoubleVector:
                offsets[prop.id] = builder.CreateNumpyVector(np.array(val, dtype=np.float64))
            elif prop._ob_type == OBXPropertyType_Flex:
                flex_builder = flatbuffers.flexbuffers.Builder()
                flex_builder.Add(val)
                buffer = flex_builder.Finish()
                offsets[prop.id] = builder.CreateByteVector(bytes(buffer))
            else:
                assert False, "programming error - invalid type OB & FB type combination"

        # start the FlatBuffers object with the largest number of properties that were ever present in the Entity
        builder.StartObject(self._last_property_iduid.id)

        # add properties to the FB object
        for prop in self._properties:
            prop_id = prop.id
            if prop_id in offsets:
                val = offsets[prop_id]
                if val:
                    builder.PrependUOffsetTRelative(val)
            else:
                val = id if prop == self._id_property else self._get_value(object, prop)
                if prop._ob_type == OBXPropertyType_Date:
                    val = date_value_to_int(val, 1000)  # convert to milliseconds
                elif prop._ob_type == OBXPropertyType_DateNano:
                    val = date_value_to_int(val, 1000000000)  # convert to nanoseconds
                builder.Prepend(prop._fb_type, val)

            builder.Slot(prop._fb_slot)

        builder.Finish(builder.EndObject())
        return builder.Output()

    def _unmarshal(self, data: bytes):
        pos = flatbuffers.encode.Get(flatbuffers.packer.uoffset, data, 0)
        table = flatbuffers.Table(data, pos)

        # initialize an empty object
        obj = self._user_type()

        # fill it with the data read from FlatBuffers
        for prop in self._properties:
            o = table.Offset(prop._fb_v_offset)
            val = None
            ob_type = prop._ob_type
            if not o:
                val = prop._py_type()  # use default (empty) value if not present in the object
            elif ob_type == OBXPropertyType_String:
                val = table.String(o + table.Pos).decode('utf-8')
            elif ob_type == OBXPropertyType_BoolVector:
                val = table.GetVectorAsNumpy(flatbuffers.number_types.BoolFlags, o)
            elif ob_type == OBXPropertyType_ByteVector:
                # access the FB byte vector information
                start = table.Vector(o)
                size = table.VectorLen(o)
                # slice the vector as a requested type
                val = prop._py_type(table.Bytes[start:start + size])
            elif ob_type == OBXPropertyType_ShortVector:
                val = table.GetVectorAsNumpy(flatbuffers.number_types.Int16Flags, o)
            elif ob_type == OBXPropertyType_CharVector:
                val = table.GetVectorAsNumpy(flatbuffers.number_types.Int16Flags, o)
            elif ob_type == OBXPropertyType_Date:
                val = table.Get(prop._fb_type, o + table.Pos)  # int
                if prop._py_type == datetime:
                    val = datetime.fromtimestamp(val / 1000.0, tz=timezone.utc)
                elif prop._py_type == float:
                    val = val / 1000.0
            elif ob_type == OBXPropertyType_DateNano and prop._py_type == datetime:
                val = table.Get(prop._fb_type, o + table.Pos)  # int
                if prop._py_type == datetime:
                    val = datetime.fromtimestamp(val / 1000000000.0, tz=timezone.utc)
                elif prop._py_type == float:
                    val = val / 1000000000.0
            elif ob_type == OBXPropertyType_IntVector:
                val = table.GetVectorAsNumpy(flatbuffers.number_types.Int32Flags, o)
            elif ob_type == OBXPropertyType_LongVector:
                val = table.GetVectorAsNumpy(flatbuffers.number_types.Int64Flags, o)
            elif ob_type == OBXPropertyType_FloatVector:
                val = table.GetVectorAsNumpy(flatbuffers.number_types.Float32Flags, o)
            elif ob_type == OBXPropertyType_DoubleVector:
                val = table.GetVectorAsNumpy(flatbuffers.number_types.Float64Flags, o)
            elif ob_type == OBXPropertyType_Flex:
                # access the FB byte vector information
                start = table.Vector(o)
                size = table.VectorLen(o)
                # slice the vector as bytes
                buf = table.Bytes[start:start + size]
                val = flatbuffers.flexbuffers.Loads(buf)
            else:
                val = table.Get(prop._fb_type, o + table.Pos)
            if prop._py_type == list:
                val = val.tolist()
            setattr(obj, prop.name, val)
        return obj

# Dictionary of entity types (metadata) collected by the Entity decorator.
# Note: using a list not a set to keep the order of entities as they were defined (set would not be deterministic).
obx_models_by_name: Dict[str, List[_Entity]] = {}


def Entity(uid: int = 0, model: str = "default") -> Callable[[Type], _Entity]:
    """ Entity decorator that wraps _Entity to allow @Entity(id=, uid=); i.e. no class arguments. """

    def wrapper(class_):
        # Also allow defining properties as class members; we'll instantiate them here
        class_members = inspect.getmembers(class_, lambda a: (inspect.isclass(a) and issubclass(a, Property)))
        for name, member_type in class_members:
            assert issubclass(member_type, Property)
            # noinspection PyArgumentList
            obj = member_type()  # Subclasses of Property have no constructor arguments
            setattr(class_, name, obj)

        types = obx_models_by_name.get(model)
        if types is None:
            types = []
            obx_models_by_name[model] = types

        entity_type = _Entity(class_, uid)
        for existing in types:
            if existing._name == entity_type._name:
                # OK for tests, where multiple models are created with the same entity name
                logging.warning(f"Model \"{model}\" already contains an entity type \"{entity_type._name}\"; replacing it.")
                types.remove(existing)
                break

        obx_models_by_name[model].append(entity_type)
        logging.info(f"Entity type {entity_type._name} added to model {model}")
        return entity_type

    return wrapper
