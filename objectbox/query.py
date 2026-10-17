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

from __future__ import annotations

from datetime import datetime

from objectbox.c import *
from objectbox.exceptions import IllegalArgumentError
from objectbox.model.properties import PropertyType
from objectbox.utils import date_value_to_int

if TYPE_CHECKING:
    import numpy as np


class Query:
    """
    Query is a reusable object that allows you to find objects in the database.
    It is created by calling ``Box.query()`` with conditions inside and finalizing with ``build()``.
    Note: Query objects are not thread-safe and should not be shared between threads.
    """
    def __init__(self, c_query, box: 'Box', alias_property_ids: Optional[Dict[str, int]] = None):
        """ This is an internal constructor. Use ``Box.query()`` instead. """
        self._c_query = c_query
        self._box = box
        self._entity = self._box._entity
        self._store = box._store
        self._alias_property_ids = alias_property_ids or {}

    def find(self) -> list:
        """ Finds a list of objects matching query. """
        with self._store.read_tx():  # We need a read transaction to ensure the object data stays valid
            # OBX_bytes_array*
            c_bytes_array_p = obx_query_find(self._c_query)
            try:
                # OBX_bytes_array
                c_bytes_array = c_bytes_array_p.contents

                result = []
                for i in range(c_bytes_array.count):
                    # OBX_bytes
                    c_bytes = c_bytes_array.data[i]
                    data = c_voidp_as_bytes(c_bytes.data, c_bytes.size)
                    result.append(self._box._entity._unmarshal(data))
                return result
            finally:
                obx_bytes_array_free(c_bytes_array_p)

    def find_ids(self) -> List[int]:
        """ Finds a list of object IDs matching query.
        The result is sorted by ID (ascending order), unless an order was set (see ``QueryBuilder.order()``). """
        c_id_array_p = obx_query_find_ids(self._c_query)
        try:
            c_id_array: OBX_id_array = c_id_array_p.contents
            if c_id_array.count == 0:
                return []
            ids = ctypes.cast(c_id_array.ids, ctypes.POINTER(obx_id * c_id_array.count))
            return list(ids.contents)
        finally:
            obx_id_array_free(c_id_array_p)

    def find_with_scores(self):
        """ Finds objects matching the query associated to their query score (e.g. distance in NN search).
        The result is sorted by score in ascending order. """
        with self._store.read_tx():  # We need a read transaction to ensure the object data stays valid
            c_bytes_score_array_p = obx_query_find_with_scores(self._c_query)
            try:
                # OBX_bytes_score_array
                c_bytes_score_array: OBX_bytes_score_array = c_bytes_score_array_p.contents
                result = []
                for i in range(c_bytes_score_array.count):
                    c_bytes_score: OBX_bytes_score = c_bytes_score_array.bytes_scores[i]
                    data = c_voidp_as_bytes(c_bytes_score.data, c_bytes_score.size)
                    score = c_bytes_score.score

                    object_ = self._box._entity._unmarshal(data)
                    result.append((object_, score))
                return result
            finally:
                obx_bytes_score_array_free(c_bytes_score_array_p)

    def find_ids_with_scores(self) -> List[Tuple[int, float]]:
        """ Finds object IDs matching the query associated to their query score (e.g. distance in NN search).
        The resulting list is sorted by score in ascending order. """
        c_id_score_array_p = obx_query_find_ids_with_scores(self._c_query)
        try:
            # OBX_id_score_array
            c_id_score_array: OBX_bytes_score_array = c_id_score_array_p.contents
            result = []
            for i in range(c_id_score_array.count):
                c_id_score: OBX_id_score = c_id_score_array.ids_scores[i]
                result.append((c_id_score.id, c_id_score.score))
            return result
        finally:
            obx_id_score_array_free(c_id_score_array_p)

    def find_ids_by_score(self) -> List[int]:
        """ Finds object IDs matching the query ordered by their query score (e.g. distance in NN search).
        The resulting list of IDs is sorted by score in ascending order. """
        # TODO extract utility function for ID array conversion
        c_id_array_p = obx_query_find_ids_by_score(self._c_query)
        try:
            c_id_array: OBX_id_array = c_id_array_p.contents
            if c_id_array.count == 0:
                return []
            ids = ctypes.cast(c_id_array.ids, ctypes.POINTER(obx_id * c_id_array.count))
            return list(ids.contents)
        finally:
            obx_id_array_free(c_id_array_p)

    def find_ids_by_score_numpy(self) -> np.array:
        """ Finds object IDs matching the query ordered by their query score (e.g. distance in NN search).
        The resulting list of IDs is sorted by score in ascending order. """
        # TODO extract utility function for ID array conversion
        c_id_array_p = obx_query_find_ids_by_score(self._c_query)
        try:
            c_id_array: OBX_id_array = c_id_array_p.contents
            c_count = c_id_array.count
            import numpy as np
            numpy_array = np.empty(c_count, dtype=np.uint64)
            if c_count > 0:
                c_ids = ctypes.cast(c_id_array.ids, ctypes.POINTER(obx_id))
                ctypes.memmove(numpy_array.ctypes.data, c_ids, numpy_array.nbytes)
            return numpy_array
        finally:
            obx_id_array_free(c_id_array_p)

    def count(self) -> int:
        """ Counts the objects that are matched by this query.
        In other words, it gives the size of the result set). """
        count = ctypes.c_uint64()
        obx_query_count(self._c_query, ctypes.byref(count))
        return int(count.value)

    def remove(self) -> int:
        """ Removes the objects that are matched by this query.

        :return: Number of objects removed.
        """
        count = ctypes.c_uint64()
        obx_query_remove(self._c_query, ctypes.byref(count))
        return int(count.value)

    def offset(self, offset: int) -> 'Query':
        """ Configure an offset for this query.
         All methods that support offset will return/process objects starting at this offset.
         Example use case: use together with limit to get a slice of the whole result, e.g. for "result paging".
         Call with offset=0 to reset to the default behavior, i.e. starting from the first element. """
        obx_query_offset(self._c_query, offset)
        return self

    def limit(self, limit: int) -> 'Query':
        """ Configure a limit for this query.
         All methods that support limit will return/process only the given number of objects.
         Example use case: use together with offset to get a slice of the whole result, e.g. for "result paging".
         Call with limit=0 to reset to the default behavior - zero limit means no limit applied. """
        obx_query_limit(self._c_query, limit)
        return self

    @overload
    def set_parameter(self, prop: Union[int, str, 'Property'],
                      value: Union[str, int, float, bytes, datetime]) -> 'Query': ...

    @overload
    def set_parameter(self, prop: Union[int, str, 'Property'],
                      value: Union[List[str], List[int], List[float], List[datetime], np.ndarray]) -> 'Query': ...

    def set_parameter(self, prop, value) -> 'Query':
        """ Changes the value of the query condition on the given property, e.g. a string or a number, the list of
        a "one of" condition or the vector of a nearest neighbor search. The type of the property decides which
        kind of value is set; e.g. a list sets the vector for a vector property and the "one of" values otherwise.
        For conditions with two values (e.g. ``between()``), use :meth:`set_parameters`.
        If there are multiple conditions on the property, give them an alias and use :meth:`set_parameter_alias`.

        Example: ``query.set_parameter(Person.name, "Joe")``

        :param prop:
            The property (or its name or ID).
        :param value:
            A string, integer, float, bytes, or a list of strings or integers ("one of" conditions), or a vector
            (list or numpy array of floats). For a nearest neighbor search, an integer sets the maximum result count.
            For ``Date``/``DateNano`` properties, also a ``datetime`` (or a float with seconds; integers are taken
            as they are, i.e. milliseconds or nanoseconds).
        :return:
            This query (to chain calls).
        :raises TypeError:
            If the value does not fit the property type.
        """
        prop_id = self._entity._get_property_id(prop)
        kind, value = _parameter_value(self._property_type(prop_id), value)
        return self._set_parameter(prop_id, None, kind, value)

    @overload
    def set_parameter_alias(self, alias: str, value: Union[str, int, float, bytes, datetime]) -> 'Query': ...

    @overload
    def set_parameter_alias(self, alias: str,
                            value: Union[List[str], List[int], List[float], List[datetime], np.ndarray]) -> 'Query':
        ...

    def set_parameter_alias(self, alias: str, value) -> 'Query':
        """ Like :meth:`set_parameter`, for the condition having the given alias
        (see ``PropertyQueryCondition.alias()``).

        Example: ``query.set_parameter_alias("name", "Joe")``

        For an alias set via ``QueryBuilder.alias()``, the property is unknown, so the value decides; e.g. a float
        sets a floating point value. ``datetime`` values are not supported then: pass milliseconds (``Date``) or
        nanoseconds (``DateNano``) instead.
        """
        prop_type = self._alias_property_type(alias)
        type_size = None
        if prop_type is None and (isinstance(value, (list, tuple)) or is_ndarray(value)):
            # 0 for non-scalar types (strings, vectors), so it tells integer lists from vectors
            type_size = obx_query_param_alias_get_type_size(self._c_query, c_str(alias))
        kind, value = _parameter_value(prop_type, value, type_size)
        return self._set_parameter(None, alias, kind, value)

    def set_parameters(self, prop: Union[int, str, 'Property'], value_a: Union[int, float, datetime],
                       value_b: Union[int, float, datetime]) -> 'Query':
        """ Changes the two values of the query condition on the given property, i.e. the range of ``between()``.
        The type of the property decides how; see :meth:`set_parameter` for single values.

        Example: ``query.set_parameters(Person.age, 18, 30)``

        :return:
            This query (to chain calls).
        :raises TypeError:
            If the values do not fit the property type.
        """
        prop_id = self._entity._get_property_id(prop)
        kind, value_a, value_b = _parameter_values(self._property_type(prop_id), value_a, value_b)
        return self._set_parameter(prop_id, None, kind, value_a, value_b)

    def set_parameters_alias(self, alias: str, value_a: Union[int, float, datetime],
                             value_b: Union[int, float, datetime]) -> 'Query':
        """ Like :meth:`set_parameters`, for the condition having the given alias
        (see ``PropertyQueryCondition.alias()``). """
        kind, value_a, value_b = _parameter_values(self._alias_property_type(alias), value_a, value_b)
        return self._set_parameter(None, alias, kind, value_a, value_b)

    def describe_parameters(self) -> str:
        """ Describes the query conditions with their current parameter values, e.g. for logging or debugging. """
        return obx_query_describe_params(self._c_query).decode('utf-8')

    def _set_parameter(self, prop_id: Optional[int], alias: Optional[str], kind: str, *values) -> 'Query':
        """ Calls the C function for the kind of parameter (see _parameter_functions) for the property or alias. """
        if kind == "ints":  # The C API has separate functions for 32-bit and 64-bit integer properties
            if alias is None:
                type_size = obx_query_param_get_type_size(self._c_query, self._entity._id, prop_id)
            else:
                type_size = obx_query_param_alias_get_type_size(self._c_query, c_str(alias))
            kind = "int32s" if type_size == 4 else "int64s"
        by_property, by_alias, to_c_args = _parameter_functions[kind]
        if alias is None:
            by_property(self._c_query, self._entity._id, prop_id, *to_c_args(*values))
        else:
            by_alias(self._c_query, c_str(alias), *to_c_args(*values))
        return self

    def _property_type(self, prop_id: int) -> int:
        for prop in self._entity._properties:
            if prop.id == prop_id:
                return prop._ob_type
        raise IllegalArgumentError(f"Property ID {prop_id} not found in entity {self._entity._name}")

    def _alias_property_type(self, alias: str) -> Optional[int]:
        """ None if the property is unknown, i.e. the alias was set via QueryBuilder.alias(). """
        prop_id = self._alias_property_ids.get(alias)
        return self._property_type(prop_id) if prop_id is not None else None


# Kind of parameter: (C function by property, C function by alias, converts the value(s) to the C arguments)
_parameter_functions = {
    "string": (obx_query_param_string, obx_query_param_alias_string, lambda v: (c_str(v),)),
    "strings": (obx_query_param_strings, obx_query_param_alias_strings,
                lambda v: (c_array([c_str(s) for s in v], ctypes.c_char_p), len(v))),
    "int": (obx_query_param_int, obx_query_param_alias_int, lambda v: (v,)),
    "int32s": (obx_query_param_int32s, obx_query_param_alias_int32s,
               lambda v: (c_array(v, ctypes.c_int32), len(v))),
    "int64s": (obx_query_param_int64s, obx_query_param_alias_int64s,
               lambda v: (c_array(v, ctypes.c_int64), len(v))),
    "2ints": (obx_query_param_2ints, obx_query_param_alias_2ints, lambda a, b: (a, b)),
    "double": (obx_query_param_double, obx_query_param_alias_double, lambda v: (v,)),
    "2doubles": (obx_query_param_2doubles, obx_query_param_alias_2doubles, lambda a, b: (a, b)),
    "bytes": (obx_query_param_bytes, obx_query_param_alias_bytes, lambda v: (bytes(v), len(v))),
    "vector_f32": (obx_query_param_vector_float32, obx_query_param_alias_vector_float32,
                   lambda v: (c_array(v, ctypes.c_float), len(v))),
}


def _parameter_value(prop_type: Optional[int], value, type_size: Optional[int] = None) -> Tuple[str, Any]:
    """ Returns the kind of parameter (see _parameter_functions) and the (converted) value.
    The property type is None if unknown (alias set via QueryBuilder.alias()); then the value decides, and for
    lists, the type size (0 for strings and vectors). """
    if isinstance(value, (list, tuple)) or is_ndarray(value):
        if prop_type == OBXPropertyType_FloatVector or (prop_type is None and (is_ndarray(value) or (
                value and not type_size and not all(isinstance(v, str) for v in value)))):
            if is_ndarray(value):
                if value.dtype != "float32":
                    raise TypeError(f"A numpy vector must have dtype float32, got: {value.dtype}")
            elif not all(_is_number(v) for v in value):
                raise TypeError("A vector parameter must be a list of numbers or a numpy array")
            return "vector_f32", value
        if prop_type == OBXPropertyType_String or (prop_type is None and not type_size):
            if not all(isinstance(v, str) for v in value):
                raise TypeError("The values for a string property must be strings")
            return "strings", value
        if prop_type is None or prop_type in _integer_types:
            return "ints", [_int_parameter(prop_type, v) for v in value]
        raise TypeError(f"A list parameter is not supported for property type {_type_name(prop_type)}")
    if isinstance(value, str):
        if prop_type not in (None, OBXPropertyType_String):
            raise TypeError(f"A string value does not fit property type {_type_name(prop_type)}")
        return "string", value
    if isinstance(value, (bytes, bytearray)):
        if prop_type not in (None, OBXPropertyType_ByteVector):
            raise TypeError(f"A bytes value does not fit property type {_type_name(prop_type)}")
        return "bytes", value
    if prop_type in _float_types or (prop_type is None and isinstance(value, float)):
        if not _is_number(value):
            raise TypeError(f"A {type(value).__name__} value does not fit property type {_type_name(prop_type)}")
        return "double", float(value)
    # Integer types; vector properties take an int as the maximum result count of a nearest neighbor search
    if prop_type is None or prop_type in _integer_types or prop_type == OBXPropertyType_FloatVector:
        return "int", _int_parameter(prop_type, value)
    raise TypeError(f"A {type(value).__name__} value does not fit property type {_type_name(prop_type)}")


def _parameter_values(prop_type: Optional[int], value_a, value_b) -> Tuple[str, Any, Any]:
    """ Like _parameter_value() for two values (e.g. between). """
    if prop_type in _float_types or (prop_type is None and (isinstance(value_a, float) or isinstance(value_b, float))):
        if not _is_number(value_a) or not _is_number(value_b):
            raise TypeError(f"Two numbers expected for property type {_type_name(prop_type)}")
        return "2doubles", float(value_a), float(value_b)
    if prop_type is None or prop_type in _integer_types:
        return "2ints", _int_parameter(prop_type, value_a), _int_parameter(prop_type, value_b)
    raise TypeError(f"Two values are not supported for property type {_type_name(prop_type)}")


_integer_types = (OBXPropertyType_Bool, OBXPropertyType_Byte, OBXPropertyType_Short, OBXPropertyType_Char,
                  OBXPropertyType_Int, OBXPropertyType_Long, OBXPropertyType_Relation, OBXPropertyType_Date,
                  OBXPropertyType_DateNano)
_float_types = (OBXPropertyType_Float, OBXPropertyType_Double)


def _is_number(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _int_parameter(prop_type: Optional[int], value) -> int:
    """ Converts dates (datetime or float seconds) to milliseconds or nanoseconds for Date/DateNano properties. """
    if prop_type == OBXPropertyType_Date:
        return date_value_to_int(value, 1000)
    if prop_type == OBXPropertyType_DateNano:
        return date_value_to_int(value, 1000000000)
    if not isinstance(value, int):
        raise TypeError(f"A {type(value).__name__} value does not fit property type {_type_name(prop_type)}")
    return value


def _type_name(prop_type: Optional[int]) -> str:
    if prop_type is None:
        return "unknown (alias set via QueryBuilder.alias())"
    try:
        return PropertyType(prop_type).name
    except ValueError:
        return str(prop_type)
