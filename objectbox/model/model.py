from objectbox.model.entity import _Entity
from objectbox.c import *

from typing import List


class IdUid:
    __slots__ = 'id', 'uid'

    def __init__(self, id: int, uid: int):
        self.id = id
        self.uid = uid


class Model:
    last_entity: IdUid
    last_index: IdUid
    last_relation: IdUid

    retired_entity_uids: List[int]
    retired_property_uids: List[int]
    retired_index_uids: List[int]
    retired_relation_uids: List[int]

    def __init__(self):
        self.__entities: List[type] = list()
        self.__model = obx_model_create()

    def entity(self, entity: _Entity):
        if not isinstance(entity, _Entity):
            raise ValueError("Given type is not an Entity. Are you passing an instance instead of a type or did you "
                             "forget the '@Entity' annotation?")

        obx_model_entity(self.__model, c_str(entity.name), entity.id, entity.uid)

        for v in entity.properties:
            obx_model_property(self.__model, c_str(v._Property__name), v._Property__ob_type, v._Property__id, v._Property__uid)
