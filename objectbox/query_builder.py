import ctypes
import numpy as np
from typing import *

from objectbox.model.properties import Property
from objectbox.objectbox import ObjectBox
from objectbox.query import Query
from objectbox.c import *


class QueryBuilder:
    def __init__(self, ob: ObjectBox, box: 'Box'):
        self._box = box
        self._entity = box._entity
        self._c_builder = obx_query_builder(ob._c_store, box._entity.id)

    def _get_property_id(self, prop: Union[int, str, Property]) -> int:
        if type(prop) is int:
            return prop
        elif type(prop) is str:
            prop = self._entity.get_property(prop)
        return prop._id

    def close(self) -> int:
        return obx_qb_close(self._c_builder)

    def error_code(self) -> int:
        return obx_qb_error_code(self._c_builder)

    def error_message(self) -> str:
        return obx_qb_error_message(self._c_builder)

    def equals_string(self, prop: Union[int, str, Property], value: str, case_sensitive: bool = True):
        prop_id = self._get_property_id(prop)
        obx_qb_equals_string(self._c_builder, prop_id, c_str(value), case_sensitive)
        return self

    def not_equals_string(self, prop: Union[int, str, Property], value: str, case_sensitive: bool = True):
        prop_id = self._get_property_id(prop)
        obx_qb_not_equals_string(self._c_builder, prop_id, c_str(value), case_sensitive)
        return self

    def contains_string(self, prop: Union[int, str, Property], value: str, case_sensitive: bool = True):
        prop_id = self._get_property_id(prop)
        obx_qb_contains_string(self._c_builder, prop_id, c_str(value), case_sensitive)
        return self

    def starts_with_string(self, prop: Union[int, str, Property], value: str, case_sensitive: bool = True):
        prop_id = self._get_property_id(prop)
        obx_qb_starts_with_string(self._c_builder, prop_id, c_str(value), case_sensitive)
        return self

    def ends_with_string(self, prop: Union[int, str, Property], value: str, case_sensitive: bool = True):
        prop_id = self._get_property_id(prop)
        obx_qb_ends_with_string(self._c_builder, prop_id, c_str(value), case_sensitive)
        return self

    def greater_than_string(self, prop: Union[int, str, Property], value: str, case_sensitive: bool = True):
        prop_id = self._get_property_id(prop)
        obx_qb_greater_than_string(self._c_builder, prop_id, c_str(value), case_sensitive)
        return self

    def greater_or_equal_string(self, prop: Union[int, str, Property], value: str, case_sensitive: bool = True):
        prop_id = self._get_property_id(prop)
        obx_qb_greater_or_equal_string(self._c_builder, prop_id, c_str(value), case_sensitive)
        return self

    def less_than_string(self, prop: Union[int, str, Property], value: str, case_sensitive: bool = True):
        prop_id = self._get_property_id(prop)
        obx_qb_less_than_string(self._c_builder, prop_id, c_str(value), case_sensitive)
        return self

    def less_or_equal_string(self, prop: Union[int, str, Property], value: str, case_sensitive: bool = True):
        prop_id = self._get_property_id(prop)
        obx_qb_less_or_equal_string(self._c_builder, prop_id, c_str(value), case_sensitive)
        return self

    def equals_int(self, prop: Union[int, str, Property], value: int):
        prop_id = self._get_property_id(prop)
        obx_qb_equals_int(self._c_builder, prop_id, value)
        return self

    def not_equals_int(self, prop: Union[int, str, Property], value: int):
        prop_id = self._get_property_id(prop)
        obx_qb_not_equals_int(self._c_builder, prop_id, value)
        return self

    def greater_than_int(self, prop: Union[int, str, Property], value: int):
        prop_id = self._get_property_id(prop)
        obx_qb_greater_than_int(self._c_builder, prop_id, value)
        return self

    def greater_or_equal_int(self, prop: Union[int, str, Property], value: int):
        prop_id = self._get_property_id(prop)
        obx_qb_greater_or_equal_int(self._c_builder, prop_id, value)
        return self

    def less_than_int(self, prop: Union[int, str, Property], value: int):
        prop_id = self._get_property_id(prop)
        obx_qb_less_than_int(self._c_builder, prop_id, value)
        return self

    def less_or_equal_int(self, prop: Union[int, str, Property], value: int):
        prop_id = self._get_property_id(prop)
        obx_qb_less_or_equal_int(self._c_builder, prop_id, value)
        return self

    def between_2ints(self, prop: Union[int, str, Property], value_a: int, value_b: int):
        prop_id = self._get_property_id(prop)
        obx_qb_between_2ints(self._c_builder, prop_id, value_a, value_b)
        return self

    def nearest_neighbors_f32(self, prop: Union[int, str, Property], query_vector: Union[np.ndarray, List[float]],
                              element_count: int):
        if isinstance(query_vector, np.ndarray):
            if query_vector.dtype != np.float32:
                raise Exception(f"query_vector dtype must be float32")
            query_vector_data = query_vector.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
        else:  # List[float]
            query_vector_data = (ctypes.c_float * len(query_vector))(*query_vector)

        prop_id = self._get_property_id(prop)
        obx_qb_nearest_neighbors_f32(self._c_builder, prop_id, query_vector_data, element_count)
        return self

    def build(self) -> Query:
        c_query = obx_query(self._c_builder)
        return Query(c_query, self._box)
