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

from array import array
from datetime import datetime, timezone
import logging
from objectbox import experimental
from objectbox.c import *
from objectbox.model.codegen import CodegenBuilder, same_values, absent_value_factory
from objectbox.model.fast_builder import FastBuilder
from objectbox.model.iduid import IdUid
from objectbox.model.properties import Property
from objectbox.utils import date_value_to_int
import threading
from typing import Optional


def camel_case(name: str) -> str:
    """ Converts a snake_case name to camelCase, e.g. "date_created" to "dateCreated" (or "vec_2d" to "vec2d").
    Leading and trailing underscores are kept, e.g. "_internal_value" becomes "_internalValue". """
    core = name.strip("_")
    if "_" not in core:
        return name
    leading = name[:len(name) - len(name.lstrip("_"))]
    trailing = name[len(name.rstrip("_")):]
    parts = [part for part in core.split("_") if part]
    return leading + parts[0] + "".join(part[:1].upper() + part[1:] for part in parts[1:]) + trailing


# _Entity class holds model information as well as conversions between python objects and FlatBuffers (ObjectBox data)
class _Entity(object):
    def __init__(self, user_type, uid: int = 0, python_names: bool = False):
        self._user_type = user_type
        self._iduid = IdUid(0, uid)
        self._name = user_type.__name__
        self._python_names = python_names
        self._last_property_iduid = IdUid(0, 0)

        self._properties: List[Property] = list()  # List[Property]
        self._offset_properties = list()  # List[Property]
        self._id_property = None
        self._fill_properties()
        self._tl = threading.local()
        self._fast_builder = None  # experimental; created on first use after a sync
        self._codegen_builder = None  # experimental; created on first use after a sync
        self._flags = 0

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
        self._fast_builder = None  # IDs (FlatBuffers slots) may have changed
        self._codegen_builder = None

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

        props_by_db_name = {}
        for prop_name, prop in variables.items():
            prop.name = prop_name
            prop._db_name = prop_name if self._python_names else camel_case(prop_name)
            other = props_by_db_name.get(prop._db_name)
            if other is not None:
                raise ValueError(f"Properties \"{other.name}\" and \"{prop.name}\" of entity {self._name} both have the "
                                 f"name \"{prop._db_name}\" in the database (camelCase); rename one of them or use "
                                 f"@Entity(python_names=True)")
            props_by_db_name[prop._db_name] = prop
            self._properties.append(prop)

            if prop.is_id():
                if self._id_property:
                    raise Exception(f"Duplicate ID property: \"{self._id_property.name}\" and \"{prop.name}\"")
                self._id_property = prop

            if prop._fb_format == 'I':  # an offset
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
        if prop._is_ndarray:
            import numpy as np  # imported already: _py_type is numpy.ndarray
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

    def _marshal(self, object, id: int) -> Union[bytes, bytearray]:
        mode = experimental._flatbuffers_mode
        if mode is None:
            return self._marshal_builder(object, id)
        # Concurrent first calls may create one builder each; equal, so either is fine.
        # Created (and codegen compiled) outside the try below: a failure there must raise, not fall back silently.
        if mode == experimental.CODEGEN:
            builder = self._codegen_builder
            if builder is None:
                builder = self._codegen_builder = CodegenBuilder(self)
        else:
            builder = self._fast_builder
            if builder is None:
                builder = self._fast_builder = FastBuilder(self)
        marshal = builder.marshal
        try:
            data = marshal(object, id)
        except Exception:
            # Values the experimental builders reject (e.g. out of range): the reference raises its usual error
            data = None
        verify = experimental._flatbuffers_verify
        if data is None or verify:
            reference = bytes(self._marshal_builder(object, id))
            if data is None:
                if verify:
                    raise AssertionError(f"Experimental FlatBuffers {mode} failed for {self._name}, "
                                         f"but the reference did not")
                return reference
            if data != reference:
                raise AssertionError(f"Experimental FlatBuffers {mode}: bytes differ from the reference for "
                                     f"{self._name}:\n  {mode}: {data.hex()}\n  reference: {reference.hex()}")
        return data

    def _marshal_builder(self, object, id: int) -> bytearray:
        """Marshals with the generic flatbuffers.Builder; the reference for the experimental fast builder."""
        import flatbuffers  # imported on first use: flatbuffers imports numpy anyway
        import numpy as np
        if not hasattr(self._tl, "builder"):
            self._tl.builder = flatbuffers.Builder(256)
        builder = self._tl.builder
        builder.Clear()

        # prepare some properties that need to be built in FB before starting the main object
        offsets = {}
        nulls = set()  # IDs of properties set to None: left out of the object (null; Flex stores None as a value)
        for prop in self._offset_properties:
            val = self._get_value(object, prop)
            if val is None and prop._ob_type != OBXPropertyType_Flex:
                nulls.add(prop.id)
                continue
            if prop._ob_type == OBXPropertyType_String:
                offsets[prop.id] = builder.CreateString(val.encode('utf-8'))
            elif prop._ob_type == OBXPropertyType_BoolVector:
                # Using a numpy bool as it seems to be more consistent in terms of size. TBD
                # https://numpy.org/doc/stable/reference/arrays.scalars.html#numpy.bool
                offsets[prop.id] = builder.CreateNumpyVector(np.array(val, dtype=np.bool_))
            elif prop._ob_type == OBXPropertyType_ByteVector:
                if prop._py_type == list:  # Int8List: signed bytes
                    val = array('b', val).tobytes()
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
                import flatbuffers.flexbuffers
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
            elif prop_id in nulls:
                continue
            else:
                val = id if prop == self._id_property else self._get_value(object, prop)
                if val is None:
                    continue  # null: no field, no vtable slot
                if prop._ob_type == OBXPropertyType_Date:
                    val = date_value_to_int(val, 1000)  # convert to milliseconds
                elif prop._ob_type == OBXPropertyType_DateNano:
                    val = date_value_to_int(val, 1000000000)  # convert to nanoseconds
                builder.Prepend(prop._fb_type, val)

            builder.Slot(prop._fb_slot)

        builder.Finish(builder.EndObject())
        return builder.Output()

    def _unmarshal(self, data: bytes):
        if experimental._flatbuffers_mode != experimental.CODEGEN:
            return self._unmarshal_table(data)
        codegen = self._codegen_builder
        if codegen is None:  # as in _marshal: outside the try, concurrent first calls are fine
            codegen = self._codegen_builder = CodegenBuilder(self)
        unmarshal = codegen.unmarshal  # compiled on first use, outside the try (as in _marshal)
        try:
            obj = unmarshal(data)
            failed = False
        except Exception:
            # Invalid data or values the reference cannot read either: it raises its usual error
            obj, failed = None, True
        verify = experimental._flatbuffers_verify
        if failed or verify:
            reference = self._unmarshal_table(data)
            if failed:
                if verify:
                    raise AssertionError(f"Experimental FlatBuffers codegen failed to unmarshal {self._name}, "
                                         f"but the reference did not")
                return reference
            for prop in self._properties:
                value, expected = getattr(obj, prop.name), getattr(reference, prop.name)
                if not same_values(value, expected):
                    raise AssertionError(f"Experimental FlatBuffers codegen: unmarshalled {self._name}.{prop.name} "
                                         f"differs from the reference:\n  codegen:   {value!r}\n  reference: {expected!r}")
        return obj

    def _unmarshal_table(self, data: bytes):
        """Unmarshals with flatbuffers.Table; the reference for the experimental codegen."""
        import flatbuffers  # imported on first use: flatbuffers imports numpy (if available)
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
                setattr(obj, prop.name, absent_value_factory(prop)())  # default (empty) value if not present
                continue
            elif ob_type == OBXPropertyType_String:
                val = table.String(o + table.Pos).decode('utf-8')
            elif ob_type == OBXPropertyType_BoolVector:
                val = table.GetVectorAsNumpy(flatbuffers.number_types.BoolFlags, o)
            elif ob_type == OBXPropertyType_ByteVector:
                # access the FB byte vector information
                start = table.Vector(o)
                size = table.VectorLen(o)
                # slice the vector as a requested type
                if prop._py_type == list:  # Int8List: signed bytes
                    val = array('b', table.Bytes[start:start + size])  # .tolist() below
                else:
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
                import flatbuffers.flexbuffers
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


# Entity flags set on a plain class by a decorator applied before @Entity() (i.e. below it), e.g. @SyncEntity();
# @Entity() moves them to the _Entity and removes the attribute.
_ENTITY_FLAGS_ATTR = "_objectbox_entity_flags"


def Entity(uid: int = 0, model: str = "default", python_names: bool = False) -> _Entity:
    """
    Entity decorator for user classes using syntax ``@Entity([uid=])`` 
    
    Example::
    
        @Entity()
        class MyEntity:
            id = Id
            name = String(index=Index)
            date_created = Date

    Property names are stored in camelCase in the database and the model JSON file (e.g. ``dateCreated`` for the
    attribute ``date_created``), like in the other ObjectBox languages, e.g. to share the model with them for Sync.
    The Python code always uses the attribute names. Set ``python_names=True`` to store the names as written in Python.
    A model JSON file with the other form of a name (e.g. ``date_created`` from versions before 5.0) is matched and
    renamed, keeping the property's data.

    Wraps the given user classes as an ``_Entity`` helper class.
    """

    def wrapper(class_) -> Callable[[Type], _Entity]:
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

        flags = class_.__dict__.get(_ENTITY_FLAGS_ATTR, 0)  # Only the class's own, not inherited ones
        if _ENTITY_FLAGS_ATTR in class_.__dict__:
            delattr(class_, _ENTITY_FLAGS_ATTR)
        entity_type = _Entity(class_, uid, python_names)
        entity_type._flags |= flags
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


def SyncEntity(entity=None, *, shared_global_ids: bool = False):
    """
    Decorator enabling Sync for an entity, i.e. its objects are synchronized with the Sync server.
    Use it together with ``@Entity()``, in any order (above or below it).
    Like ``@Entity()``, it is used with parentheses; ``@SyncEntity`` without parentheses works too.

    Note: Sync cannot be enabled for an existing (non-synced) entity, and synced entities can only have relations to
    other synced entities.

    :param shared_global_ids:
        Set to True to use shared global IDs for this entity: object IDs are then the same on all Sync clients instead
        of being mapped between local and global IDs (the default). Only use this if IDs are unique across all
        clients (e.g. assigned IDs); otherwise, clients overwrite each other's objects. Cannot be changed later.

    Example::

        @SyncEntity()
        @Entity()
        class MyEntity:
            id = Id
            name = String
    """
    flags = OBXEntityFlags.SYNC_ENABLED
    if shared_global_ids:
        flags |= OBXEntityFlags.SHARED_GLOBAL_IDS

    def wrapper(entity_to_sync):
        if isinstance(entity_to_sync, _Entity):  # Above @Entity()
            entity_to_sync._flags |= flags
        elif inspect.isclass(entity_to_sync):  # Below @Entity(): it takes the flags from the class
            setattr(entity_to_sync, _ENTITY_FLAGS_ATTR, entity_to_sync.__dict__.get(_ENTITY_FLAGS_ATTR, 0) | flags)
        else:
            raise TypeError("@SyncEntity() must be applied to an entity class (together with @Entity())")
        return entity_to_sync

    if entity is None:  # Used with parentheses: @SyncEntity()
        return wrapper
    return wrapper(entity)
