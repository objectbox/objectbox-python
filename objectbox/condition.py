from __future__ import annotations

from enum import Enum
from typing import *
import numpy as np

if TYPE_CHECKING:
    from objectbox.c import obx_qb_cond
    from objectbox.query_builder import QueryBuilder


class QueryCondition:
    def and_(self, other: QueryCondition) -> QueryCondition:
        return LogicQueryCondition(self, other, LogicQueryConditionOp.AND)
    __and__ = and_

    def or_(self, other: QueryCondition) -> QueryCondition:
        return LogicQueryCondition(self, other, LogicQueryConditionOp.OR)
    __or__ = or_

    def apply(self, qb: QueryBuilder) -> obx_qb_cond:
        """ Applies the QueryCondition to the supplied QueryBuilder.

        :return:
            The C handle for the applied condition.
        """
        raise NotImplementedError


class LogicQueryConditionOp(Enum):
    AND = 1
    OR = 2


class LogicQueryCondition(QueryCondition):
    """ A QueryCondition describing a logical operation between two inner QueryCondition's (e.g. AND/OR). """

    def __init__(self, cond1: QueryCondition, cond2: QueryCondition, op: LogicQueryConditionOp):
        self._cond1 = cond1
        self._cond2 = cond2
        self._op = op

    def _apply_conditions(self, qb: QueryBuilder) -> List[obx_qb_cond]:
        return [self._cond1.apply(qb), self._cond2.apply(qb)]

    def _apply_and(self, qb: QueryBuilder) -> obx_qb_cond:
        return qb.all(self._apply_conditions(qb))

    def _apply_or(self, qb: QueryBuilder) -> obx_qb_cond:
        return qb.any(self._apply_conditions(qb))

    def apply(self, qb: QueryBuilder) -> obx_qb_cond:
        if self._op == LogicQueryConditionOp.AND:
            return self._apply_and(qb)
        elif self._op == LogicQueryConditionOp.OR:
            return self._apply_or(qb)
        else:
            raise Exception(f"Unknown LogicQueryCondition op: {self._op.name}")


class PropertyQueryConditionOp(Enum):
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


class PropertyQueryCondition(QueryCondition):
    """ A QueryCondition describing an operation to be applied on a property (e.g. name == "John", age == 24) """

    _OP_MAP: Dict[PropertyQueryConditionOp, str] = {
        PropertyQueryConditionOp.EQ: "_apply_eq",
        PropertyQueryConditionOp.NOT_EQ: "_apply_not_eq",
        PropertyQueryConditionOp.CONTAINS: "_apply_contains",
        PropertyQueryConditionOp.STARTS_WITH: "_apply_starts_with",
        PropertyQueryConditionOp.ENDS_WITH: "_apply_ends_with",
        PropertyQueryConditionOp.GT: "_apply_gt",
        PropertyQueryConditionOp.GTE: "_apply_gte",
        PropertyQueryConditionOp.LT: "_apply_lt",
        PropertyQueryConditionOp.LTE: "_apply_lte",
        PropertyQueryConditionOp.BETWEEN: "_apply_between",
        PropertyQueryConditionOp.NEAREST_NEIGHBOR: "_apply_nearest_neighbor",
        PropertyQueryConditionOp.CONTAINS_KEY_VALUE: "_contains_key_value"
        # ... new property query conditions here ... :)
    }

    def __init__(self, property_id: int, op: PropertyQueryConditionOp, args: Dict[str, Any]):
        if op not in self._OP_MAP:
            raise Exception(f"Invalid PropertyQueryConditionOp: {op}")
        op_func_name = self._OP_MAP[op]
        if not hasattr(self, op_func_name):
            raise Exception(f"Missing PropertyQueryCondition op function: {op_func_name} (op: {op})")
        op_func = getattr(self, op_func_name)

        self._property_id = property_id
        self._op = op
        self._op_func = op_func
        self._args = args
        self._alias = None

    def alias(self, value: str):
        """ Sets an alias for this condition that can later be used with Query's set_parameter_* methods. """
        self._alias = value
        return self

    def _apply_eq(self, qb: QueryBuilder) -> obx_qb_cond:
        value = self._args['value']
        case_sensitive = self._args['case_sensitive']
        if isinstance(value, str):
            return qb.equals_string(self._property_id, value, case_sensitive)
        elif isinstance(value, int):
            return qb.equals_int(self._property_id, value)
        else:
            raise Exception(f"Unsupported type for 'EQ': {type(value)}")

    def _apply_not_eq(self, qb: QueryBuilder) -> obx_qb_cond:
        value = self._args['value']
        case_sensitive = self._args['case_sensitive']
        if isinstance(value, str):
            return qb.not_equals_string(self._property_id, value, case_sensitive)
        elif isinstance(value, int):
            return qb.not_equals_int(self._property_id, value)
        else:
            raise Exception(f"Unsupported type for 'NOT_EQ': {type(value)}")

    def _apply_contains(self, qb: QueryBuilder) -> obx_qb_cond:
        value = self._args['value']
        case_sensitive = self._args['case_sensitive']
        if isinstance(value, str):
            return qb.contains_string(self._property_id, value, case_sensitive)
        else:
            raise Exception(f"Unsupported type for 'CONTAINS': {type(value)}")

    def _apply_starts_with(self, qb: QueryBuilder) -> obx_qb_cond:
        value = self._args['value']
        case_sensitive = self._args['case_sensitive']
        if isinstance(value, str):
            return qb.starts_with_string(self._property_id, value, case_sensitive)
        else:
            raise Exception(f"Unsupported type for 'STARTS_WITH': {type(value)}")

    def _apply_ends_with(self, qb: QueryBuilder) -> obx_qb_cond:
        value = self._args['value']
        case_sensitive = self._args['case_sensitive']
        if isinstance(value, str):
            return qb.ends_with_string(self._property_id, value, case_sensitive)
        else:
            raise Exception(f"Unsupported type for 'ENDS_WITH': {type(value)}")

    def _apply_gt(self, qb: QueryBuilder) -> obx_qb_cond:
        value = self._args['value']
        case_sensitive = self._args['case_sensitive']
        if isinstance(value, str):
            return qb.greater_than_string(self._property_id, value, case_sensitive)
        elif isinstance(value, int):
            return qb.greater_than_int(self._property_id, value)
        else:
            raise Exception(f"Unsupported type for 'GT': {type(value)}")

    def _apply_gte(self, qb: QueryBuilder) -> obx_qb_cond:
        value = self._args['value']
        case_sensitive = self._args['case_sensitive']
        if isinstance(value, str):
            return qb.greater_or_equal_string(self._property_id, value, case_sensitive)
        elif isinstance(value, int):
            return qb.greater_or_equal_int(self._property_id, value)
        else:
            raise Exception(f"Unsupported type for 'GTE': {type(value)}")

    def _apply_lt(self, qb: QueryBuilder) -> obx_qb_cond:
        value = self._args['value']
        case_sensitive = self._args['case_sensitive']
        if isinstance(value, str):
            return qb.less_than_string(self._property_id, value, case_sensitive)
        elif isinstance(value, int):
            return qb.less_than_int(self._property_id, value)
        else:
            raise Exception("Unsupported type for 'LT': " + str(type(value)))

    def _apply_lte(self, qb: QueryBuilder) -> obx_qb_cond:
        value = self._args['value']
        case_sensitive = self._args['case_sensitive']
        if isinstance(value, str):
            return qb.less_or_equal_string(self._property_id, value, case_sensitive)
        elif isinstance(value, int):
            return qb.less_or_equal_int(self._property_id, value)
        else:
            raise Exception(f"Unsupported type for 'LTE': {type(value)}")

    def _apply_between(self, qb: QueryBuilder) -> obx_qb_cond:
        a = self._args['a']
        b = self._args['b']
        if isinstance(a, int):
            return qb.between_2ints(self._property_id, a, b)
        else:
            raise Exception(f"Unsupported type for 'BETWEEN': {type(a)}")

    def _apply_nearest_neighbor(self, qb: QueryBuilder) -> obx_qb_cond:
        query_vector = self._args['query_vector']
        element_count = self._args['element_count']

        if len(query_vector) == 0:
            raise Exception("query_vector can't be empty")

        is_float_vector = False
        is_float_vector |= isinstance(query_vector, np.ndarray) and query_vector.dtype == np.float32
        is_float_vector |= isinstance(query_vector, list) and type(query_vector[0]) == float
        if is_float_vector:
            return qb.nearest_neighbors_f32(self._property_id, query_vector, element_count)
        else:
            raise Exception(f"Unsupported type for 'NEAREST_NEIGHBOR': {type(query_vector)}")

    def _contains_key_value(self, qb: QueryBuilder) -> obx_qb_cond:
        key = self._args['key']
        value = self._args['value']
        case_sensitive = self._args['case_sensitive']
        return qb.contains_key_value(self._property_id, key, value, case_sensitive)

    def apply(self, qb: QueryBuilder) -> obx_qb_cond:
        c_cond = self._op_func(qb)
        if self._alias is not None:
            qb.alias(self._alias)
        return c_cond
