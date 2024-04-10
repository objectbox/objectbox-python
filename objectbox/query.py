# Copyright 2019-2023 ObjectBox Ltd. All rights reserved.
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
        self._ob = box._ob

    def find(self) -> list:
        """ Finds a list of objects matching query. """
        with self._ob.read_tx():
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
            result = []
            for i in range(c_id_array.count):
                result.append(c_id_array.ids[i])
            return result
        finally:
            obx_id_array_free(c_id_array_p)

    def find_with_scores(self):
        """ Finds objects matching the query associated to their query score (e.g. distance in NN search).
        The result is sorted by score in ascending order. """
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

    def count(self) -> int:
        count = ctypes.c_uint64()
        obx_query_count(self._c_query, ctypes.byref(count))
        return int(count.value)
    
    def remove(self) -> int:
        count = ctypes.c_uint64()
        obx_query_remove(self._c_query, ctypes.byref(count))
        return int(count.value)
    
    def offset(self, offset: int):
        return obx_query_offset(self._c_query, offset)
    
    def limit(self, limit: int):
        return obx_query_limit(self._c_query, limit)
