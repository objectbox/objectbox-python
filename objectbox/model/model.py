from objectbox.model import Entity
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

    __entities: List[type]

    def __init__(self):
        self.__entities = list()

    def add_entity(self, entity_type: type):
        if not issubclass(entity_type, Entity):
            raise ValueError("given type is not a subclass of 'Entity'")

        self.__entities.append(entity_type)
