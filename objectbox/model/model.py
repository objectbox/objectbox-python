# Copyright 2019-2021 ObjectBox Ltd. All rights reserved.
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


from objectbox.model.entity import _Entity
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

    def entity(self, entity: _Entity, last_property_id: IdUid):
        if not isinstance(entity, _Entity):
            raise Exception("Given type is not an Entity. Are you passing an instance instead of a type or did you "
                            "forget the '@Entity' annotation?")

        entity.last_property_id = last_property_id

        obx_model_entity(self._c_model, c_str(
            entity.name), entity.id, entity.uid)

        for v in entity.properties:
            obx_model_property(self._c_model, c_str(
                v._name), v._ob_type, v._id, v._uid)
            if v._flags != 0:
                obx_model_property_flags(self._c_model, v._flags)

        obx_model_entity_last_property_id(
            self._c_model, last_property_id.id, last_property_id.uid)

    # called by Builder
    def _finish(self):
        if self.last_relation_id:
            obx_model_last_relation_id(
                self._c_model, self.last_relation_id.id, self.last_relation_id.uid)

        if self.last_index_id:
            obx_model_last_index_id(
                self._c_model, self.last_index_id.id, self.last_index_id.uid)

        if self.last_entity_id:
            obx_model_last_entity_id(
                self._c_model, self.last_entity_id.id, self.last_entity_id.uid)
