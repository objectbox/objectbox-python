from enum import Enum

class _ConditionOp(Enum):
    eq = 1
    notEq = 2
    contains = 3
    startsWith = 4
    endsWith = 5
    gt = 6
    greaterOrEq = 7
    lt = 8
    lessOrEq = 9
    between = 10


class QueryCondition:
    def __init__(self, property_id: int, op: _ConditionOp, value, value_b = None, case_sensitive: bool = True):
        self._property_id = property_id
        self._op = op
        self._value = value
        self._value_b = value_b
        self._case_sensitive = case_sensitive

    def apply(self, builder: 'QueryBuilder'):
        if self._op == _ConditionOp.eq:
            if isinstance(self._value, str):
                builder.equals_string(self._property_id, self._value, self._case_sensitive)
            elif isinstance(self._value, int):
                builder.equals_int(self._property_id, self._value)
            else:
                raise Exception("Unsupported type for 'eq': " + str(type(self._value)))
        
        elif self._op == _ConditionOp.notEq:
            if isinstance(self._value, str):
                builder.not_equals_string(self._property_id, self._value, self._case_sensitive)
            elif isinstance(self._value, int):
                builder.not_equals_int(self._property_id, self._value)
            else:
                raise Exception("Unsupported type for 'notEq': " + str(type(self._value)))
        
        elif self._op == _ConditionOp.contains:
            if isinstance(self._value, str):
                builder.contains_string(self._property_id, self._value, self._case_sensitive)
            else:
                raise Exception("Unsupported type for 'contains': " + str(type(self._value)))
        
        elif self._op == _ConditionOp.startsWith:
            if isinstance(self._value, str):
                builder.starts_with_string(self._property_id, self._value, self._case_sensitive)
            else:
                raise Exception("Unsupported type for 'startsWith': " + str(type(self._value)))
        
        elif self._op == _ConditionOp.endsWith:
            if isinstance(self._value, str):
                builder.ends_with_string(self._property_id, self._value, self._case_sensitive)
            else:
                raise Exception("Unsupported type for 'endsWith': " + str(type(self._value)))
        
        elif self._op == _ConditionOp.gt:
            if isinstance(self._value, str):
                builder.greater_than_string(self._property_id, self._value, self._case_sensitive)
            elif isinstance(self._value, int):
                builder.greater_than_int(self._property_id, self._value)
            else:
                raise Exception("Unsupported type for 'gt': " + str(type(self._value)))
        
        elif self._op == _ConditionOp.greaterOrEq:
            if isinstance(self._value, str):
                builder.greater_or_equal_string(self._property_id, self._value, self._case_sensitive)
            elif isinstance(self._value, int):
                builder.greater_or_equal_int(self._property_id, self._value)
            else:
                raise Exception("Unsupported type for 'greaterOrEq': " + str(type(self._value)))
        
        elif self._op == _ConditionOp.lt:
            if isinstance(self._value, str):
                builder.less_than_string(self._property_id, self._value, self._case_sensitive)
            elif isinstance(self._value, int):
                builder.less_than_int(self._property_id, self._value)
            else:
                raise Exception("Unsupported type for 'lt': " + str(type(self._value)))
        
        elif self._op == _ConditionOp.lessOrEq:
            if isinstance(self._value, str):
                builder.less_or_equal_string(self._property_id, self._value, self._case_sensitive)
            elif isinstance(self._value, int):
                builder.less_or_equal_int(self._property_id, self._value)
            else:
                raise Exception("Unsupported type for 'lessOrEq': " + str(type(self._value)))
            
        elif self._op == _ConditionOp.between:
            if isinstance(self._value, int):
                builder.between_2ints(self._property_id, self._value, self._value_b)
            else:
                raise Exception("Unsupported type for 'between': " + str(type(self._value)))