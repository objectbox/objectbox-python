from __future__ import annotations

import ctypes
from enum import IntEnum
from typing import *

from objectbox.c import *
from objectbox.condition import QueryCondition
from objectbox.exceptions import IllegalArgumentError, IllegalStateError
from objectbox.model.properties import Property, Relation
from objectbox.store import Store
from objectbox.query import Query
from objectbox.utils import check_float_vector

if TYPE_CHECKING:
    import numpy as np


class OrderFlags(IntEnum):
    """ Flags to adjust the order of query results, see :func:`QueryBuilder.order`.
    Combine multiple flags using ``|``. """

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
        self._c_builder_or_none = obx_query_builder(store._c_store, box._entity._id)  # None once closed
        # Entity and property ID of the conditions' aliases; for Query.set_parameter_alias()
        self._alias_properties: Dict[str, Tuple['_Entity', int]] = {}
        self._root: Optional[QueryBuilder] = None  # For a builder of a linked entity (see link()): the query's builder
        store._add_native_resource(self)

    @property
    def _c_builder(self):
        root = self._root or self
        if root._c_builder_or_none is None:
            self._box._store._c_store  # Raises if the store is closed (which closed the builder)
            raise IllegalStateError("The query builder is closed: build() closes it")
        return self._c_builder_or_none

    def _linked(self, c_builder, entity: '_Entity', condition: Optional[QueryCondition]) -> 'QueryBuilder':
        """ Creates the builder for a linked entity, owned by the C builder of the query. """
        linked = QueryBuilder.__new__(QueryBuilder)
        linked._box = self._box
        linked._entity = entity
        linked._c_builder_or_none = c_builder  # Owned by the root's C builder
        linked._alias_properties = self._alias_properties
        linked._root = self._root or self
        if condition is not None:
            condition.apply(linked)
        return linked

    def _assert_root(self, method: str):
        if self._root is not None:
            raise IllegalStateError(f"{method}() is not supported on the builder of a linked entity (returned by "
                                    f"link() or backlink()); call it on the query's builder (e.g. from box.query())")

    def link(self, relation: Relation, condition: Optional[QueryCondition] = None) -> 'QueryBuilder':
        """ Adds conditions on the target of a to-one relation of this builder's entity: matches objects whose
        related object matches the condition. Returns the builder of the target entity, e.g. to link further.
        Results are still objects of the query's entity.

        Example (orders of customers named "Ann")::

            qb = box.query(Order.text.starts_with("A"))
            qb.link(Order.customer_id, Customer.name.equals("Ann"))
            query = qb.build()

        :param relation:
            A :class:`Relation` property of this builder's entity.
        :param condition:
            The condition(s) on the target entity (optional, e.g. to only link further).
        :return:
            The builder of the target entity; call ``build()`` on the query's builder, not on this one.
        """
        self._assert_relation(relation)
        if relation._entity._name != self._entity._name:
            raise IllegalArgumentError(f"link(): relation {relation._entity._name}.{relation.name} is not a property "
                                       f"of entity {self._entity._name}")
        target = self._entity_by_name(relation._target_name)
        return self._linked(obx_qb_link_property(self._c_builder, relation.id), target, condition)

    def backlink(self, relation: Relation, condition: Optional[QueryCondition] = None) -> 'QueryBuilder':
        """ Adds conditions on the objects whose to-one relation points to the objects of this builder's entity
        (the relation used in reverse): matches objects referred to by at least one object that matches the condition.
        Returns the builder of the relation's entity, e.g. to link further.
        Results are still objects of the query's entity.

        Example (customers with an order of more than 100)::

            qb = customer_box.query()
            qb.backlink(Order.customer_id, Order.total.greater_than(100))
            query = qb.build()

        :param relation:
            A :class:`Relation` property of another entity (or of this one) targeting this builder's entity.
        :param condition:
            The condition(s) on the relation's entity (optional, e.g. to only link further).
        :return:
            The builder of the relation's entity; call ``build()`` on the query's builder, not on this one.
        """
        self._assert_relation(relation)
        if relation._target_name != self._entity._name:
            raise IllegalArgumentError(f"backlink(): relation {relation._entity._name}.{relation.name} targets entity "
                                       f"{relation._target_name}, not {self._entity._name}")
        source = self._entity_by_name(relation._entity._name)
        c_builder = obx_qb_backlink_property(self._c_builder, source._id, relation.id)
        return self._linked(c_builder, source, condition)

    @staticmethod
    def _assert_relation(relation):
        if not isinstance(relation, Relation):
            raise TypeError(f"Expected a Relation property, got {relation!r}")
        relation._assert_ids_assigned()

    def _entity_by_name(self, name: str) -> '_Entity':
        """ The entity of the store's model (the entity of a relation may be an equal one of another model). """
        model = self._box._store._model
        if model is not None:
            for entity in model.entities:
                if entity._name == name:
                    return entity
        raise IllegalArgumentError(f"Entity {name} is not in the store's model")

    def close(self):
        """ Closes the builder, freeing its native resources; ``build()`` does this, so only needed for a builder
        that is not built. Closing again does nothing. """
        self._assert_root("close")
        c_builder = self._c_builder_or_none
        if c_builder is not None:
            self._c_builder_or_none = None
            self._box._store._remove_native_resource(self)
            obx_qb_close(c_builder)

    def __del__(self):
        if getattr(self, "_root", True) is None:  # A root builder (a linked one is owned by it)
            try:
                self.close()
            except Exception:  # E.g. during interpreter shutdown
                pass

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

    def order(self, prop: Union[int, str, Property], flags: Union[OrderFlags, int] = 0) -> 'QueryBuilder':
        """ Orders the query results by the given property, ascending by default.
        Call multiple times to order by multiple properties: the first call sets the primary order,
        the following ones are used for results that are equal according to the preceding orders.
        Applies to ``find()`` and ``find_ids()``; note that ordering requires to sort all matching objects.

        Example: ``box.query(Person.age.greater_than(17)).order(Person.name).build()``

        :param prop:
            The property (or its name or ID) to order by.
        :param flags:
            :class:`OrderFlags` to adjust the order; combine multiple using ``|``,
            e.g. ``OrderFlags.DESCENDING | OrderFlags.CASE_SENSITIVE``.
        :return:
            This QueryBuilder (to chain calls).
        """
        self._assert_root("order")  # The core ignores orders of linked entities
        prop_id = self._entity._get_property_id(prop)
        obx_qb_order(self._c_builder, prop_id, flags)
        return self

    def order_desc(self, prop: Union[int, str, Property], flags: Union[OrderFlags, int] = 0) -> 'QueryBuilder':
        """ Orders the query results by the given property, descending;
        the same as ``order(prop, OrderFlags.DESCENDING | flags)``, see :meth:`order`.

        Example: ``box.query().order_desc(Person.age).build()``

        :param prop:
            The property (or its name or ID) to order by.
        :param flags:
            Further :class:`OrderFlags` to adjust the order, e.g. ``OrderFlags.CASE_SENSITIVE``.
        :return:
            This QueryBuilder (to chain calls).
        """
        return self.order(prop, OrderFlags.DESCENDING | flags)

    def build(self) -> Query:
        """ Builds the query; this closes the builder (it can not be used afterwards). """
        self._assert_root("build")
        try:
            c_query = obx_query(self._c_builder)
        finally:
            self.close()
        return Query(c_query, self._box, self._alias_properties)

    def alias(self, alias: str):
        obx_qb_param_alias(self._c_builder, c_str(alias))
        return self

    def _alias_for_property(self, alias: str, prop_id: int):
        """ Like alias(), also remembering the condition's property (for Query.set_parameter_alias()). """
        self._alias_properties[alias] = (self._entity, prop_id)
        return self.alias(alias)
