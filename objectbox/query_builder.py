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

    def close(self) -> int:
        return obx_qb_close(self._c_builder)

    def error_code(self) -> int:
        return obx_qb_error_code(self._c_builder)

    def error_message(self) -> str:
        return obx_qb_error_message(self._c_builder)

    def equals_string(self, prop: Union[int, str, Property], value: str, case_sensitive: bool = True) -> obx_qb_cond:
        prop_id = self._entity.get_property_id(prop)
        cond = obx_qb_equals_string(self._c_builder, prop_id, c_str(value), case_sensitive)
        return cond

    def not_equals_string(self, prop: Union[int, str, Property], value: str,
                          case_sensitive: bool = True) -> obx_qb_cond:
        prop_id = self._entity.get_property_id(prop)
        cond = obx_qb_not_equals_string(self._c_builder, prop_id, c_str(value), case_sensitive)
        return cond

    def contains_string(self, prop: Union[int, str, Property], value: str, case_sensitive: bool = True) -> obx_qb_cond:
        prop_id = self._entity.get_property_id(prop)
        cond = obx_qb_contains_string(self._c_builder, prop_id, c_str(value), case_sensitive)
        return cond

    def starts_with_string(self, prop: Union[int, str, Property], value: str,
                           case_sensitive: bool = True) -> obx_qb_cond:
        prop_id = self._entity.get_property_id(prop)
        cond = obx_qb_starts_with_string(self._c_builder, prop_id, c_str(value), case_sensitive)
        return cond

    def ends_with_string(self, prop: Union[int, str, Property], value: str, case_sensitive: bool = True) -> obx_qb_cond:
        prop_id = self._entity.get_property_id(prop)
        cond = obx_qb_ends_with_string(self._c_builder, prop_id, c_str(value), case_sensitive)
        return cond

    def greater_than_string(self, prop: Union[int, str, Property], value: str,
                            case_sensitive: bool = True) -> obx_qb_cond:
        prop_id = self._entity.get_property_id(prop)
        cond = obx_qb_greater_than_string(self._c_builder, prop_id, c_str(value), case_sensitive)
        return cond

    def greater_or_equal_string(self, prop: Union[int, str, Property], value: str,
                                case_sensitive: bool = True) -> obx_qb_cond:
        prop_id = self._entity.get_property_id(prop)
        cond = obx_qb_greater_or_equal_string(self._c_builder, prop_id, c_str(value), case_sensitive)
        return cond

    def less_than_string(self, prop: Union[int, str, Property], value: str, case_sensitive: bool = True) -> obx_qb_cond:
        prop_id = self._entity.get_property_id(prop)
        cond = obx_qb_less_than_string(self._c_builder, prop_id, c_str(value), case_sensitive)
        return cond

    def less_or_equal_string(self, prop: Union[int, str, Property], value: str,
                             case_sensitive: bool = True) -> obx_qb_cond:
        prop_id = self._entity.get_property_id(prop)
        cond = obx_qb_less_or_equal_string(self._c_builder, prop_id, c_str(value), case_sensitive)
        return cond

    def equals_int(self, prop: Union[int, str, Property], value: int) -> obx_qb_cond:
        prop_id = self._entity.get_property_id(prop)
        cond = obx_qb_equals_int(self._c_builder, prop_id, value)
        return cond

    def not_equals_int(self, prop: Union[int, str, Property], value: int) -> obx_qb_cond:
        prop_id = self._entity.get_property_id(prop)
        cond = obx_qb_not_equals_int(self._c_builder, prop_id, value)
        return cond

    def greater_than_int(self, prop: Union[int, str, Property], value: int) -> obx_qb_cond:
        prop_id = self._entity.get_property_id(prop)
        cond = obx_qb_greater_than_int(self._c_builder, prop_id, value)
        return cond

    def greater_or_equal_int(self, prop: Union[int, str, Property], value: int) -> obx_qb_cond:
        prop_id = self._entity.get_property_id(prop)
        cond = obx_qb_greater_or_equal_int(self._c_builder, prop_id, value)
        return cond

    def less_than_int(self, prop: Union[int, str, Property], value: int) -> obx_qb_cond:
        prop_id = self._entity.get_property_id(prop)
        cond = obx_qb_less_than_int(self._c_builder, prop_id, value)
        return cond

    def less_or_equal_int(self, prop: Union[int, str, Property], value: int) -> obx_qb_cond:
        prop_id = self._entity.get_property_id(prop)
        cond = obx_qb_less_or_equal_int(self._c_builder, prop_id, value)
        return cond

    def between_2ints(self, prop: Union[int, str, Property], value_a: int, value_b: int) -> obx_qb_cond:
        prop_id = self._entity.get_property_id(prop)
        cond = obx_qb_between_2ints(self._c_builder, prop_id, value_a, value_b)
        return cond

    def nearest_neighbors_f32(self, prop: Union[int, str, Property], query_vector: Union[np.ndarray, List[float]],
                              element_count: int):
        if isinstance(query_vector, np.ndarray) and query_vector.dtype != np.float32:
            raise Exception(f"query_vector dtype is expected to be np.float32, got: {query_vector.dtype}")
        prop_id = self._entity.get_property_id(prop)
        c_query_vector = c_array(query_vector, ctypes.c_float)
        cond = obx_qb_nearest_neighbors_f32(self._c_builder, prop_id, c_query_vector, element_count)
        return cond

    def any(self, conditions: List[obx_qb_cond]) -> obx_qb_cond:
        c_conditions = c_array(conditions, obx_qb_cond)
        cond = obx_qb_any(self._c_builder, c_conditions, len(conditions))
        return cond

    def all(self, conditions: List[obx_qb_cond]) -> obx_qb_cond:
        c_conditions = c_array_pointer(conditions, obx_qb_cond)
        cond = obx_qb_all(self._c_builder, c_conditions, len(conditions))
        return cond

    def build(self) -> Query:
        c_query = obx_query(self._c_builder)
        return Query(c_query, self._box)

    def alias(self, alias: str):
        obx_qb_param_alias(self._c_builder, c_str(alias))
        return self
