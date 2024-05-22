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
from objectbox.c import *
from objectbox.model.iduid import IdUid
from objectbox.model.entity import _Entity
from objectbox.model.properties import *


class Model:
    def __init__(self):
        self.entities: List[_Entity] = []

        self.last_entity_iduid = IdUid(0, 0)
        self.last_index_iduid = IdUid(0, 0)
        self.last_relation_iduid = IdUid(0, 0)

        self._c_model = None

    def entity(self, entity: _Entity):
        if not isinstance(entity, _Entity):
            raise Exception(f"Given type is not an Entity ({type(entity)}). "
                            f"Maybe did you forget the @Entity annotation?")
        for other_entity in self.entities:  # Linear search (we should't have many entities)
            if entity.name == other_entity.name:
                raise Exception(f"Duplicate entity: \"{entity.name}\"")
        self.entities.append(entity)

    def validate_ids_assigned(self):
        if not self.last_entity_iduid.is_assigned():
            raise Exception("Model last_entity_id not assigned")
        if not self.last_entity_iduid.is_assigned():
            raise ValueError("Model last_index_id not assigned")
        # if not self.last_relation_id.is_assigned(): TODO last_relation_id
        #     return False
        # TODO validate last_entity_id value
        # TODO validate last_index_id value
        for entity in self.entities:
            if not entity.iduid.is_assigned():
                raise ValueError(f"Entity \"{entity.name}\" id not assigned")
            for prop in entity.properties:
                # TODO validate last_property_id value
                if not prop.iduid.is_assigned():
                    raise ValueError(f"Property \"{entity.name}\"->\"{prop.name}\" id not assigned")
            if not entity.last_property_iduid.is_assigned():
                raise ValueError(f"Entity \"{entity.name}\" last_property_id not assigned")

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

    def _create_index(self, index: Union[Index, HnswIndex]):
        if isinstance(index, HnswIndex):
            self._set_hnsw_params(index)
        obx_model_property_index_id(self._c_model, index.id, index.uid)

    def _create_property(self, prop: Property):
        obx_model_property(self._c_model, c_str(prop.name), prop._ob_type, prop.id, prop.uid)
        if prop._flags != 0:
            obx_model_property_flags(self._c_model, prop._flags)
        if prop.index is not None:
            self._create_index(prop.index)

    def _create_entity(self, entity: _Entity):
        obx_model_entity(self._c_model, c_str(entity.name), entity.id, entity.uid)
        for prop in entity.properties:
            self._create_property(prop)
        obx_model_entity_last_property_id(self._c_model, entity.last_property_iduid.id, entity.last_property_iduid.uid)

    def _create_c_model(self) -> obx_model:  # Called by StoreOptions
        """ Creates the OBX model by invoking the C API.
        Before calling this method, IDs/UIDs must be assigned either manually or via sync_model(). """
        self._c_model = obx_model()
        for entity in self.entities:
            self._create_entity(entity)
        if self.last_relation_iduid:
            obx_model_last_relation_id(self._c_model, self.last_relation_iduid.id, self.last_relation_iduid.uid)
        if self.last_index_iduid:
            obx_model_last_index_id(self._c_model, self.last_index_iduid.id, self.last_index_iduid.uid)
        if self.last_entity_iduid:
            obx_model_last_entity_id(self._c_model, self.last_entity_iduid.id, self.last_entity_iduid.uid)
        return self._c_model
