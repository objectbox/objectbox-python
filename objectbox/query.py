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
        with self._ob.read_tx():
            # OBX_bytes_array*
            c_bytes_array_p = obx_query_find(self._c_query)

            try:
                # OBX_bytes_array
                c_bytes_array = c_bytes_array_p.contents

                result = list()
                for i in range(c_bytes_array.count):
                    # OBX_bytes
                    c_bytes = c_bytes_array.data[i]
                    data = c_voidp_as_bytes(c_bytes.data, c_bytes.size)
                    result.append(self._box._entity.unmarshal(data))

                return result
            finally:
                obx_bytes_array_free(c_bytes_array_p)

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