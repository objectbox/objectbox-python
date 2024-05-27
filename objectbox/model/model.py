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

    def on_sync(self):
        """ Method called once ID/UID are synced with the model file. """
        for entity in self.entities:
            entity._on_sync()

    def entity(self, entity: _Entity):
        if not isinstance(entity, _Entity):
            raise Exception(f"The given type is not an Entity: {type(entity)}. "
                            f"Ensure to have an @Entity annotation on the class.")
        for other_entity in self.entities:  # Linear search (we should't have many entities)
            if entity._name == other_entity._name:
                raise Exception(f"Duplicate entity: \"{entity._name}\"")
        self.entities.append(entity)

    def validate_ids_assigned(self):
        # TODO validate last_relation_iduid
        has_entities = len(self.entities) > 0
        has_indices = False
        for entity in self.entities:
            has_properties = len(entity._properties) > 0
            if not entity._iduid.is_assigned():
                raise ValueError(f"Entity \"{entity._name}\" ID/UID not assigned")
            for prop in entity._properties:
                if not prop.iduid.is_assigned():
                    raise ValueError(f"Property \"{entity._name}.{prop.name}\" ID/UID not assigned")
                if prop.index is not None:
                    has_indices = True
                    if not prop.index.iduid.is_assigned():
                        raise ValueError(f"Property index \"{entity._name}.{prop.name}\" ID/UID not assigned")
            if has_properties and not entity._last_property_iduid.is_assigned():
                raise ValueError(f"Entity \"{entity._name}\" last property ID/UID not assigned")
        if has_entities and not self.last_entity_iduid.is_assigned():
            raise ValueError("Last entity ID/UID not assigned")
        if has_indices and not self.last_index_iduid.is_assigned():
            raise ValueError("Last index ID/UID not assigned")

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
        obx_model_entity(self._c_model, c_str(entity._name), entity._id, entity._uid)
        for prop in entity._properties:
            self._create_property(prop)
        obx_model_entity_last_property_id(self._c_model, entity._last_property_iduid.id, entity._last_property_iduid.uid)

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
