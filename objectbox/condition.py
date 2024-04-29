from enum import Enum
from typing import *
import numpy as np


class _QueryConditionOp(Enum):
    EQ = 1
    NOT_EQ = 2
    CONTAINS = 3
    STARTS_WITH = 4
    ENDS_WITH = 5
    GT = 6
    GTE = 7
    LT = 8
    LTE = 9
    BETWEEN = 10
    NEAREST_NEIGHBOR = 11
    CONTAINS_KEY_VALUE = 12


class QueryCondition:
    def __init__(self, property_id: int, op: _QueryConditionOp, args: Dict[str, Any]):
        if op not in self._get_op_map():
            raise Exception(f"Invalid query condition op with ID: {op}")

        self._property_id = property_id
        self._op = op
        self._args = args
        self._alias = None

    def alias(self, value: str):
        self._alias = value
        return self

    def _get_op_map(self):
        return {
            _QueryConditionOp.EQ: self._apply_eq,
            _QueryConditionOp.NOT_EQ: self._apply_not_eq,
            _QueryConditionOp.CONTAINS: self._apply_contains,
            _QueryConditionOp.STARTS_WITH: self._apply_starts_with,
            _QueryConditionOp.ENDS_WITH: self._apply_ends_with,
            _QueryConditionOp.GT: self._apply_gt,
            _QueryConditionOp.GTE: self._apply_gte,
            _QueryConditionOp.LT: self._apply_lt,
            _QueryConditionOp.LTE: self._apply_lte,
            _QueryConditionOp.BETWEEN: self._apply_between,
            _QueryConditionOp.NEAREST_NEIGHBOR: self._apply_nearest_neighbor,
            _QueryConditionOp.CONTAINS_KEY_VALUE: self._contains_key_value
            # ... new query condition here ... :)
        }

    def _apply_eq(self, qb: 'QueryBuilder'):
        value = self._args['value']
        case_sensitive = self._args['case_sensitive']
        if isinstance(value, str):
            qb.equals_string(self._property_id, value, case_sensitive)
        elif isinstance(value, int):
            qb.equals_int(self._property_id, value)
        else:
            raise Exception(f"Unsupported type for 'EQ': {type(value)}")

    def _apply_not_eq(self, qb: 'QueryBuilder'):
        value = self._args['value']
        case_sensitive = self._args['case_sensitive']
        if isinstance(value, str):
            qb.not_equals_string(self._property_id, value, case_sensitive)
        elif isinstance(value, int):
            qb.not_equals_int(self._property_id, value)
        else:
            raise Exception(f"Unsupported type for 'NOT_EQ': {type(value)}")

    def _apply_contains(self, qb: 'QueryBuilder'):
        value = self._args['value']
        case_sensitive = self._args['case_sensitive']
        if isinstance(value, str):
            qb.contains_string(self._property_id, value, case_sensitive)
        else:
            raise Exception(f"Unsupported type for 'CONTAINS': {type(value)}")

    def _apply_starts_with(self, qb: 'QueryBuilder'):
        value = self._args['value']
        case_sensitive = self._args['case_sensitive']
        if isinstance(value, str):
            qb.starts_with_string(self._property_id, value, case_sensitive)
        else:
            raise Exception(f"Unsupported type for 'STARTS_WITH': {type(value)}")

    def _apply_ends_with(self, qb: 'QueryBuilder'):
        value = self._args['value']
        case_sensitive = self._args['case_sensitive']
        if isinstance(value, str):
            qb.ends_with_string(self._property_id, value, case_sensitive)
        else:
            raise Exception(f"Unsupported type for 'ENDS_WITH': {type(value)}")

    def _apply_gt(self, qb: 'QueryBuilder'):
        value = self._args['value']
        case_sensitive = self._args['case_sensitive']
        if isinstance(value, str):
            qb.greater_than_string(self._property_id, value, case_sensitive)
        elif isinstance(value, int):
            qb.greater_than_int(self._property_id, value)
        else:
            raise Exception(f"Unsupported type for 'GT': {type(value)}")

    def _apply_gte(self, qb: 'QueryBuilder'):
        value = self._args['value']
        case_sensitive = self._args['case_sensitive']
        if isinstance(value, str):
            qb.greater_or_equal_string(self._property_id, value, case_sensitive)
        elif isinstance(value, int):
            qb.greater_or_equal_int(self._property_id, value)
        else:
            raise Exception(f"Unsupported type for 'GTE': {type(value)}")

    def _apply_lt(self, qb: 'QueryCondition'):
        value = self._args['value']
        case_sensitive = self._args['case_sensitive']
        if isinstance(value, str):
            qb.less_than_string(self._property_id, value, case_sensitive)
        elif isinstance(value, int):
            qb.less_than_int(self._property_id, value)
        else:
            raise Exception("Unsupported type for 'LT': " + str(type(value)))

    def _apply_lte(self, qb: 'QueryBuilder'):
        value = self._args['value']
        case_sensitive = self._args['case_sensitive']
        if isinstance(value, str):
            qb.less_or_equal_string(self._property_id, value, case_sensitive)
        elif isinstance(value, int):
            qb.less_or_equal_int(self._property_id, value)
        else:
            raise Exception(f"Unsupported type for 'LTE': {type(value)}")

    def _apply_between(self, qb: 'QueryBuilder'):
        a = self._args['a']
        b = self._args['b']
        if isinstance(a, int):
            qb.between_2ints(self._property_id, a, b)
        else:
            raise Exception(f"Unsupported type for 'BETWEEN': {type(a)}")

    def _apply_nearest_neighbor(self, qb: 'QueryBuilder'):
        query_vector = self._args['query_vector']
        element_count = self._args['element_count']

        if len(query_vector) == 0:
            raise Exception("query_vector can't be empty")

        is_float_vector = False
        is_float_vector |= isinstance(query_vector, np.ndarray) and query_vector.dtype == np.float32
        is_float_vector |= isinstance(query_vector, list) and type(query_vector[0]) == float
        if is_float_vector:
            qb.nearest_neighbors_f32(self._property_id, query_vector, element_count)
        else:
            raise Exception(f"Unsupported type for 'NEAREST_NEIGHBOR': {type(query_vector)}")

    def _contains_key_value(self, qb: 'QueryBuilder'):
        key = self._args['key']
        value = self._args['value']
        case_sensitive = self._args['case_sensitive']
        qb.contains_key_value(self._property_id, key, value, case_sensitive)

    def apply(self, qb: 'QueryBuilder'):
        """ Applies the stored condition to the supplied query builder. """
        self._get_op_map()[self._op](qb)

        if self._alias is not None:
            qb.alias(self._alias)
