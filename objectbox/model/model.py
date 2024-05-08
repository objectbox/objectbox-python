# Copyright 2019-2024 ObjectBox Ltd. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from objectbox.logger import logger
from objectbox.model.entity import _Entity
from objectbox.model.properties import *
from objectbox.c import *


class IdUid:
    __slots__ = 'id', 'uid'

    def __init__(self, id: int, uid: int):
        self.id = id
        self.uid = uid

    def __bool__(self):
        return self.id != 0 or self.uid != 0


class Model:
    def __init__(self):
        self._entities = list()
        self._c_model = obx_model()
        self.last_entity_id = IdUid(0, 0)
        self.last_index_id = IdUid(0, 0)
        self.last_relation_id = IdUid(0, 0)

    def _set_hnsw_params(self, index: HnswIndex):
        if index.dimensions is not None:
            obx_model_property_index_hnsw_dimensions(self._c_model, index.dimensions)
        if index.neighbors_per_node is not None:
            obx_model_property_index_hnsw_neighbors_per_node(self._c_model, index.neighbors_per_node)
        if index.indexing_search_count is not None:
            obx_model_property_index_hnsw_indexing_search_count(self._c_model, index.indexing_search_count)
        if index.flags is not None:
            obx_model_property_index_hnsw_flags(self._c_model, index.flags)
        if index.distance_type is not None:
            obx_model_property_index_hnsw_distance_type(self._c_model, index.distance_type)
        if index.reparation_backlink_probability is not None:
            obx_model_property_index_hnsw_reparation_backlink_probability(self._c_model,
                                                                          index.reparation_backlink_probability)
        if index.vector_cache_hint_size_kb is not None:
            obx_model_property_index_hnsw_vector_cache_hint_size_kb(self._c_model, index.vector_cache_hint_size_kb)

    def entity(self, entity: _Entity, last_property_id: IdUid):
        if not isinstance(entity, _Entity):
            raise Exception("Given type is not an Entity. Are you passing an instance instead of a type or did you "
                            "forget the '@Entity' annotation?")

        entity.last_property_id = last_property_id

        obx_model_entity(self._c_model, c_str(entity.name), entity.id, entity.uid)

        logger.debug(f"Creating entity \"{entity.name}\" (ID={entity.id}, {entity.uid})")

        for property_ in entity.properties:
            obx_model_property(self._c_model, c_str(property_._name), property_._ob_type, property_._id, property_._uid)

            logger.debug(f"Creating property \"{property_._name}\" (ID={property_._id}, UID={property_._uid})")

            if property_._flags != 0:
                obx_model_property_flags(self._c_model, property_._flags)

            if property_._index is not None:
                index = property_._index
                if isinstance(index, HnswIndex):
                    self._set_hnsw_params(index)
                    logger.debug(f"  HNSW index (ID={index.id}, UID{index.uid}); Dimensions: {index.dimensions}")
                else:
                    logger.debug(f"  Index (ID={index.id}, UID{index.uid}); Type: {index.type}")
                obx_model_property_index_id(self._c_model, index.id, index.uid)

        obx_model_entity_last_property_id(self._c_model, last_property_id.id, last_property_id.uid)

    def _finish(self):  # Called by Builder
        if self.last_relation_id:
            obx_model_last_relation_id(self._c_model, self.last_relation_id.id, self.last_relation_id.uid)

        if self.last_index_id:
            obx_model_last_index_id(self._c_model, self.last_index_id.id, self.last_index_id.uid)

        if self.last_entity_id:
            obx_model_last_entity_id(self._c_model, self.last_entity_id.id, self.last_entity_id.uid)
