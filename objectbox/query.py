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

from objectbox.c import *


class Query:
    def __init__(self, c_query, box: 'Box'):
        self._c_query = c_query
        self._box = box
        self._entity = self._box._entity
        self._store = box._store

    def find(self) -> list:
        """ Finds a list of objects matching query. """
        with self._store.read_tx():  # We need a read transaction to ensure the object data stays valid
            # OBX_bytes_array*
            c_bytes_array_p = obx_query_find(self._c_query)
            try:
                # OBX_bytes_array
                c_bytes_array = c_bytes_array_p.contents

                result = []
                for i in range(c_bytes_array.count):
                    # OBX_bytes
                    c_bytes = c_bytes_array.data[i]
                    data = c_voidp_as_bytes(c_bytes.data, c_bytes.size)
                    result.append(self._box._entity.unmarshal(data))
                return result
            finally:
                obx_bytes_array_free(c_bytes_array_p)

    def find_ids(self) -> List[int]:
        """ Finds a list of object IDs matching query. The result is sorted by ID (ascending order). """
        c_id_array_p = obx_query_find_ids(self._c_query)
        try:
            c_id_array: OBX_id_array = c_id_array_p.contents
            if c_id_array.count == 0:
                return []
            ids = ctypes.cast(c_id_array.ids, ctypes.POINTER(obx_id * c_id_array.count))
            return list(ids.contents)
        finally:
            obx_id_array_free(c_id_array_p)

    def find_with_scores(self):
        """ Finds objects matching the query associated to their query score (e.g. distance in NN search).
        The result is sorted by score in ascending order. """
        with self._store.read_tx():  # We need a read transaction to ensure the object data stays valid
            c_bytes_score_array_p = obx_query_find_with_scores(self._c_query)
            try:
                # OBX_bytes_score_array
                c_bytes_score_array: OBX_bytes_score_array = c_bytes_score_array_p.contents
                result = []
                for i in range(c_bytes_score_array.count):
                    c_bytes_score: OBX_bytes_score = c_bytes_score_array.bytes_scores[i]
                    data = c_voidp_as_bytes(c_bytes_score.data, c_bytes_score.size)
                    score = c_bytes_score.score

                    object_ = self._box._entity.unmarshal(data)
                    result.append((object_, score))
                return result
            finally:
                obx_bytes_score_array_free(c_bytes_score_array_p)

    def find_ids_with_scores(self) -> List[Tuple[int, float]]:
        """ Finds object IDs matching the query associated to their query score (e.g. distance in NN search).
        The resulting list is sorted by score in ascending order. """
        c_id_score_array_p = obx_query_find_ids_with_scores(self._c_query)
        try:
            # OBX_id_score_array
            c_id_score_array: OBX_bytes_score_array = c_id_score_array_p.contents
            result = []
            for i in range(c_id_score_array.count):
                c_id_score: OBX_id_score = c_id_score_array.ids_scores[i]
                result.append((c_id_score.id, c_id_score.score))
            return result
        finally:
            obx_id_score_array_free(c_id_score_array_p)

    def find_ids_by_score(self) -> List[int]:
        """ Finds object IDs matching the query ordered by their query score (e.g. distance in NN search).
        The resulting list of IDs is sorted by score in ascending order. """
        # TODO extract utility function for ID array conversion
        c_id_array_p = obx_query_find_ids_by_score(self._c_query)
        try:
            c_id_array: OBX_id_array = c_id_array_p.contents
            if c_id_array.count == 0:
                return []
            ids = ctypes.cast(c_id_array.ids, ctypes.POINTER(obx_id * c_id_array.count))
            return list(ids.contents)
        finally:
            obx_id_array_free(c_id_array_p)

    def find_ids_by_score_numpy(self) -> np.array:
        """ Finds object IDs matching the query ordered by their query score (e.g. distance in NN search).
        The resulting list of IDs is sorted by score in ascending order. """
        # TODO extract utility function for ID array conversion
        c_id_array_p = obx_query_find_ids_by_score(self._c_query)
        try:
            c_id_array: OBX_id_array = c_id_array_p.contents
            c_count = c_id_array.count
            numpy_array = np.empty(c_count, dtype=np.uint64)
            if c_count > 0:
                c_ids = ctypes.cast(c_id_array.ids, ctypes.POINTER(obx_id))
                ctypes.memmove(numpy_array.ctypes.data, c_ids, numpy_array.nbytes)
            return numpy_array
        finally:
            obx_id_array_free(c_id_array_p)

    def count(self) -> int:
        count = ctypes.c_uint64()
        obx_query_count(self._c_query, ctypes.byref(count))
        return int(count.value)

    def remove(self) -> int:
        count = ctypes.c_uint64()
        obx_query_remove(self._c_query, ctypes.byref(count))
        return int(count.value)

    def offset(self, offset: int) -> 'Query':
        obx_query_offset(self._c_query, offset)
        return self

    def limit(self, limit: int) -> 'Query':
        obx_query_limit(self._c_query, limit)
        return self

    def set_parameter_string(self, prop: Union[int, str, 'Property'], value: str) -> 'Query':
        prop_id = self._entity.get_property_id(prop)
        obx_query_param_string(self._c_query, self._entity.id, prop_id, c_str(value))
        return self

    def set_parameter_int(self, prop: Union[int, str, 'Property'], value: int) -> 'Query':
        prop_id = self._entity.get_property_id(prop)
        obx_query_param_int(self._c_query, self._entity.id, prop_id, value)
        return self

    def set_parameter_vector_f32(self,
                                 prop: Union[int, str, 'Property'],
                                 value: Union[List[float], np.ndarray]) -> 'Query':
        if isinstance(value, np.ndarray) and value.dtype != np.float32:
            raise Exception(f"value dtype is expected to be np.float32, got: {value.dtype}")
        prop_id = self._entity.get_property_id(prop)
        c_value = c_array(value, ctypes.c_float)
        num_el = len(value)
        obx_query_param_vector_float32(self._c_query, self._entity.id, prop_id, c_value, num_el)
        return self

    def offset(self, offset: int):
        return obx_query_offset(self._c_query, offset)

    def limit(self, limit: int):
        return obx_query_limit(self._c_query, limit)

    def set_parameter_alias_string(self, alias: str, value: str):
        return obx_query_param_alias_string(self._c_query, c_str(alias), c_str(value))

    def set_parameter_alias_int(self, alias: str, value: int):
        return obx_query_param_alias_int(self._c_query, c_str(alias), value)

    def set_parameter_alias_vector_f32(self, alias: str, value: Union[List[float], np.ndarray]):
        return obx_query_param_alias_vector_float32(self._c_query, c_str(alias), c_array(value, ctypes.c_float),
                                                    len(value))
