from objectbox.model.entity import _Entity
from objectbox.objectbox import ObjectBox
from objectbox.query import Query
from objectbox.c import *


class QueryBuilder:
    def __init__(self, ob: ObjectBox, box: 'Box', entity: '_Entity', condition: 'QueryCondition'):
        if not isinstance(entity, _Entity):
            raise Exception("Given type is not an Entity")
        self._box = box
        self._entity = entity
        self._condition = condition
        self._c_builder = obx_query_builder(ob._c_store, entity.id)

    def close(self) -> int:
        return obx_qb_close(self)

    def error_code(self) -> int:
        return obx_qb_error_code(self)
    
    def error_message(self) -> str:
        return obx_qb_error_message(self)
    
    def equals_string(self, property_id: int, value: str, case_sensitive: bool):
        obx_qb_equals_string(self._c_builder, property_id, c_str(value), case_sensitive)
        return self
    
    def not_equals_string(self, property_id: int, value: str, case_sensitive: bool):
        obx_qb_not_equals_string(self._c_builder, property_id, c_str(value), case_sensitive)
        return self
    
    def contains_string(self, property_id: int, value: str, case_sensitive: bool):
        obx_qb_contains_string(self._c_builder, property_id, c_str(value), case_sensitive)
        return self
    
    def starts_with_string(self, property_id: int, value: str, case_sensitive: bool):
        obx_qb_starts_with_string(self._c_builder, property_id, c_str(value), case_sensitive)
        return self
    
    def ends_with_string(self, property_id: int, value: str, case_sensitive: bool):
        obx_qb_ends_with_string(self._c_builder, property_id, c_str(value), case_sensitive)
        return self
    
    def greater_than_string(self, property_id: int, value: str, case_sensitive: bool):
        obx_qb_greater_than_string(self._c_builder, property_id, c_str(value), case_sensitive)
        return self
    
    def greater_or_equal_string(self, property_id: int, value: str, case_sensitive: bool):
        obx_qb_greater_or_equal_string(self._c_builder, property_id, c_str(value), case_sensitive)
        return self
    
    def less_than_string(self, property_id: int, value: str, case_sensitive: bool):
        obx_qb_less_than_string(self._c_builder, property_id, c_str(value), case_sensitive)
        return self
    
    def less_or_equal_string(self, property_id: int, value: str, case_sensitive: bool):
        obx_qb_less_or_equal_string(self._c_builder, property_id, c_str(value), case_sensitive)
        return self
    
    def equals_int(self, property_id: int, value: int):
        obx_qb_equals_int(self._c_builder, property_id, value)
        return self
    
    def not_equals_int(self, property_id: int, value: int):
        obx_qb_not_equals_int(self._c_builder, property_id, value)
        return self
    
    def greater_than_int(self, property_id: int, value: int):
        obx_qb_greater_than_int(self._c_builder, property_id, value)
        return self
    
    def greater_or_equal_int(self, property_id: int, value: int):
        obx_qb_greater_or_equal_int(self._c_builder, property_id, value)
        return self
    
    def less_than_int(self, property_id: int, value: int):
        obx_qb_less_than_int(self._c_builder, property_id, value)
        return self
    
    def less_or_equal_int(self, property_id: int, value: int):
        obx_qb_less_or_equal_int(self._c_builder, property_id, value)
        return self
    
    def between_2ints(self, property_id: int, value_a: int, value_b: int):
        obx_qb_between_2ints(self._c_builder, property_id, value_a, value_b)
        return self
    
    def apply_condition(self):
        self._condition.apply(self)
    
    def build(self) -> Query:
        self.apply_condition()
        c_query = obx_query(self._c_builder)
        return Query(c_query, self._box)