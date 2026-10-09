from __future__ import annotations

import ctypes
from enum import IntEnum
from typing import *

from objectbox.c import *
from objectbox.model.properties import Property
from objectbox.store import Store
from objectbox.query import Query
from objectbox.utils import check_float_vector

if TYPE_CHECKING:
    import numpy as np


class OrderFlags(IntEnum):
    DESCENDING = OBXOrderFlags_DESCENDING
    """Reverses the order from ascending (default) to descending."""

    CASE_SENSITIVE = OBXOrderFlags_CASE_SENSITIVE
    """Sorts upper case letters before lower case letters.
    If not specified, the default is case insensitive for ASCII characters."""

    UNSIGNED = OBXOrderFlags_UNSIGNED
    """For scalars only: changes the comparison to unsigned (default is signed)."""

    NULLS_LAST = OBXOrderFlags_NULLS_LAST
    """Null values will be put last.
    If not specified, by default null values will be put first."""

    NULLS_ZERO = OBXOrderFlags_NULLS_ZERO
    """Null values should be treated equal to zero (scalars only)."""


class QueryBuilder:
    """
    Query builder
    """
    def __init__(self, store: Store, box: 'Box'):
        self._box = box
        self._entity = box._entity
        self._c_builder = obx_query_builder(store._c_store, box._entity._id)

    def close(self) -> int:
        return obx_qb_close(self._c_builder)

    def error_code(self) -> int:
        return obx_qb_error_code(self._c_builder)

    def error_message(self) -> str:
        return obx_qb_error_message(self._c_builder)

    def equals_string(self, prop: Union[int, str, Property], value: str, case_sensitive: bool = True) -> obx_qb_cond:
        prop_id = self._entity._get_property_id(prop)
        cond = obx_qb_equals_string(self._c_builder, prop_id, c_str(value), case_sensitive)
        return cond

    def not_equals_string(self, prop: Union[int, str, Property], value: str,
                          case_sensitive: bool = True) -> obx_qb_cond:
        prop_id = self._entity._get_property_id(prop)
        cond = obx_qb_not_equals_string(self._c_builder, prop_id, c_str(value), case_sensitive)
        return cond

    def contains_string(self, prop: Union[int, str, Property], value: str, case_sensitive: bool = True) -> obx_qb_cond:
        """Checks if value is contained by the given string property."""
        prop_id = self._entity._get_property_id(prop)
        cond = obx_qb_contains_string(self._c_builder, prop_id, c_str(value), case_sensitive)
        return cond

    def starts_with_string(self, prop: Union[int, str, Property], value: str,
                           case_sensitive: bool = True) -> obx_qb_cond:
        prop_id = self._entity._get_property_id(prop)
        cond = obx_qb_starts_with_string(self._c_builder, prop_id, c_str(value), case_sensitive)
        return cond

    def ends_with_string(self, prop: Union[int, str, Property], value: str, case_sensitive: bool = True) -> obx_qb_cond:
        prop_id = self._entity._get_property_id(prop)
        cond = obx_qb_ends_with_string(self._c_builder, prop_id, c_str(value), case_sensitive)
        return cond

    def greater_than_string(self, prop: Union[int, str, Property], value: str,
                            case_sensitive: bool = True) -> obx_qb_cond:
        prop_id = self._entity._get_property_id(prop)
        cond = obx_qb_greater_than_string(self._c_builder, prop_id, c_str(value), case_sensitive)
        return cond

    def greater_or_equal_string(self, prop: Union[int, str, Property], value: str,
                                case_sensitive: bool = True) -> obx_qb_cond:
        prop_id = self._entity._get_property_id(prop)
        cond = obx_qb_greater_or_equal_string(self._c_builder, prop_id, c_str(value), case_sensitive)
        return cond

    def less_than_string(self, prop: Union[int, str, Property], value: str, case_sensitive: bool = True) -> obx_qb_cond:
        prop_id = self._entity._get_property_id(prop)
        cond = obx_qb_less_than_string(self._c_builder, prop_id, c_str(value), case_sensitive)
        return cond

    def less_or_equal_string(self, prop: Union[int, str, Property], value: str,
                             case_sensitive: bool = True) -> obx_qb_cond:
        prop_id = self._entity._get_property_id(prop)
        cond = obx_qb_less_or_equal_string(self._c_builder, prop_id, c_str(value), case_sensitive)
        return cond

    def in_strings(self, prop: Union[int, str, Property], values: List[str],
                   case_sensitive: bool = True) -> obx_qb_cond:
        """ Matches if the string property equals any of the given values. """
        prop_id = self._entity._get_property_id(prop)
        # The C array references the encoded strings, so they stay alive for the duration of the call
        c_values = c_array([c_str(value) for value in values], ctypes.c_char_p)
        cond = obx_qb_in_strings(self._c_builder, prop_id, c_values, len(values), case_sensitive)
        return cond

    def equals_int(self, prop: Union[int, str, Property], value: int) -> obx_qb_cond:
        prop_id = self._entity._get_property_id(prop)
        cond = obx_qb_equals_int(self._c_builder, prop_id, value)
        return cond

    def not_equals_int(self, prop: Union[int, str, Property], value: int) -> obx_qb_cond:
        prop_id = self._entity._get_property_id(prop)
        cond = obx_qb_not_equals_int(self._c_builder, prop_id, value)
        return cond

    def in_ints(self, prop: Union[int, str, Property], values: List[int]) -> obx_qb_cond:
        """ Matches if the integer property equals any of the given values.
        Supported for 32-bit (Int32) and 64-bit (Int64, Id, Date, DateNano) integer properties. """
        prop_id = self._entity._get_property_id(prop)
        if self._is_int32_property(prop_id):
            c_values = c_array([int(value) for value in values], ctypes.c_int32)
            return obx_qb_in_int32s(self._c_builder, prop_id, c_values, len(values))
        else:
            c_values = c_array([int(value) for value in values], ctypes.c_int64)
            return obx_qb_in_int64s(self._c_builder, prop_id, c_values, len(values))

    def not_in_ints(self, prop: Union[int, str, Property], values: List[int]) -> obx_qb_cond:
        """ Matches if the integer property equals none of the given values.
        Supported for 32-bit (Int32) and 64-bit (Int64, Id, Date, DateNano) integer properties. """
        prop_id = self._entity._get_property_id(prop)
        if self._is_int32_property(prop_id):
            c_values = c_array([int(value) for value in values], ctypes.c_int32)
            return obx_qb_not_in_int32s(self._c_builder, prop_id, c_values, len(values))
        else:
            c_values = c_array([int(value) for value in values], ctypes.c_int64)
            return obx_qb_not_in_int64s(self._c_builder, prop_id, c_values, len(values))

    def _is_int32_property(self, prop_id: int) -> bool:
        """ The C API has separate functions for 32-bit and 64-bit integer properties (e.g. for "in" conditions). """
        for prop in self._entity._properties:
            if prop.id == prop_id:
                return prop._ob_type == OBXPropertyType_Int
        raise Exception(f"Property ID {prop_id} not found in Entity \"{self._entity._name}\"")

    def greater_than_int(self, prop: Union[int, str, Property], value: int) -> obx_qb_cond:
        prop_id = self._entity._get_property_id(prop)
        cond = obx_qb_greater_than_int(self._c_builder, prop_id, value)
        return cond
    
    def greater_than_double(self, prop: Union[int, str, Property], value: float) -> obx_qb_cond:
        prop_id = self._entity._get_property_id(prop)
        cond = obx_qb_greater_than_double(self._c_builder, prop_id, value)
        return cond

    def greater_or_equal_int(self, prop: Union[int, str, Property], value: int) -> obx_qb_cond:
        prop_id = self._entity._get_property_id(prop)
        cond = obx_qb_greater_or_equal_int(self._c_builder, prop_id, value)
        return cond
    
    def greater_or_equal_double(self, prop: Union[int, str, Property], value: float) -> obx_qb_cond:
        prop_id = self._entity._get_property_id(prop)
        cond = obx_qb_greater_or_equal_double(self._c_builder, prop_id, value)
        return cond

    def less_than_int(self, prop: Union[int, str, Property], value: int) -> obx_qb_cond:
        prop_id = self._entity._get_property_id(prop)
        cond = obx_qb_less_than_int(self._c_builder, prop_id, value)
        return cond
    
    def less_than_double(self, prop: Union[int, str, Property], value: float) -> obx_qb_cond:
        prop_id = self._entity._get_property_id(prop)
        cond = obx_qb_less_than_double(self._c_builder, prop_id, value)
        return cond

    def less_or_equal_int(self, prop: Union[int, str, Property], value: int) -> obx_qb_cond:
        prop_id = self._entity._get_property_id(prop)
        cond = obx_qb_less_or_equal_int(self._c_builder, prop_id, value)
        return cond
    
    def less_or_equal_double(self, prop: Union[int, str, Property], value: float) -> obx_qb_cond:
        prop_id = self._entity._get_property_id(prop)
        cond = obx_qb_less_or_equal_double(self._c_builder, prop_id, value)
        return cond

    def between_2ints(self, prop: Union[int, str, Property], value_a: int, value_b: int) -> obx_qb_cond:
        prop_id = self._entity._get_property_id(prop)
        cond = obx_qb_between_2ints(self._c_builder, prop_id, value_a, value_b)
        return cond
    
    def between_2doubles(self, prop: Union[int, str, Property], value_a: float, value_b: float) -> obx_qb_cond:
        prop_id = self._entity._get_property_id(prop)
        cond = obx_qb_between_2doubles(self._c_builder, prop_id, value_a, value_b)
        return cond

    def equals_bytes(self, prop: Union[int, str, Property], value: bytes) -> obx_qb_cond:
        prop_id = self._entity._get_property_id(prop)
        cond = obx_qb_equals_bytes(self._c_builder, prop_id, value, len(value))
        return cond
    
    def greater_than_bytes(self, prop: Union[int, str, Property], value: bytes) -> obx_qb_cond:
        prop_id = self._entity._get_property_id(prop)
        cond = obx_qb_greater_than_bytes(self._c_builder, prop_id, value, len(value))
        return cond
    
    def greater_or_equal_bytes(self, prop: Union[int, str, Property], value: bytes) -> obx_qb_cond:
        prop_id = self._entity._get_property_id(prop)
        cond = obx_qb_greater_or_equal_bytes(self._c_builder, prop_id, value, len(value))
        return cond
    
    def less_than_bytes(self, prop: Union[int, str, Property], value: bytes) -> obx_qb_cond:
        prop_id = self._entity._get_property_id(prop)
        cond = obx_qb_less_than_bytes(self._c_builder, prop_id, value, len(value))
        return cond
    
    def less_or_equal_bytes(self, prop: Union[int, str, Property], value: bytes) -> obx_qb_cond:
        prop_id = self._entity._get_property_id(prop)
        cond = obx_qb_less_or_equal_bytes(self._c_builder, prop_id, value, len(value))
        return cond
    
    def nearest_neighbors_f32(self,
                              prop: Union[int, str, Property],
                              query_vector: Union[np.ndarray, List[float]],
                              element_count: int):
        check_float_vector(query_vector, "query_vector")
        prop_id = self._entity._get_property_id(prop)
        c_query_vector = c_array(query_vector, ctypes.c_float)
        cond = obx_qb_nearest_neighbors_f32(self._c_builder, prop_id, c_query_vector, element_count)
        return cond

    def is_null(self, prop: Union[int, str, Property]) -> obx_qb_cond:
        """ Matches objects without a value for the given property (null, i.e. put with None). """
        return obx_qb_null(self._c_builder, self._entity._get_property_id(prop))

    def not_null(self, prop: Union[int, str, Property]) -> obx_qb_cond:
        """ Matches objects with a value for the given property (not null). """
        return obx_qb_not_null(self._c_builder, self._entity._get_property_id(prop))

    def contains_key_value(self, prop: Union[int, str, Property], key: str, value: str,
                           case_sensitive: bool = True) -> obx_qb_cond:
        """ Checks whether the given Flex property, interpreted as a dictionary and indexed at key, has a value
        corresponding to the given value.

        :param case_sensitive:
            If false, ignore case when matching value
        """
        prop_id = self._entity._get_property_id(prop)
        cond = obx_qb_contains_key_value_string(self._c_builder, prop_id, c_str(key), c_str(value), case_sensitive)
        return cond

    def any(self, conditions: List[obx_qb_cond]) -> obx_qb_cond:
        c_conditions = c_array(conditions, obx_qb_cond)
        cond = obx_qb_any(self._c_builder, c_conditions, len(conditions))
        return cond

    def all(self, conditions: List[obx_qb_cond]) -> obx_qb_cond:
        c_conditions = c_array_pointer(conditions, obx_qb_cond)
        cond = obx_qb_all(self._c_builder, c_conditions, len(conditions))
        return cond

    def order(self, prop: Union[int, str, Property], order_flags: OrderFlags = 0) -> 'QueryBuilder':
        """Configures an order for results in the query."""
        prop_id = self._entity._get_property_id(prop)
        obx_qb_order(self._c_builder, prop_id, order_flags)
        return self

    def build(self) -> Query:
        c_query = obx_query(self._c_builder)
        return Query(c_query, self._box)

    def alias(self, alias: str):
        obx_qb_param_alias(self._c_builder, c_str(alias))
        return self
