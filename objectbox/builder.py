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


from objectbox.c import *
from objectbox.model import Model
from objectbox.objectbox import ObjectBox
from objectbox.store_options import StoreOptions


class Builder:
    def __init__(self):
        self._model = Model()
        self._directory = None
        self._max_db_size_in_kb = None

    def directory(self, path: str) -> 'Builder':
        self._directory = path
        return self

    def max_db_size_in_kb(self, size_in_kb: int) -> 'Builder':
        self._max_db_size_in_kb = size_in_kb
        return self

    def model(self, model: Model) -> 'Builder':
        self._model = model
        self._model._finish()
        return self

    def build(self) -> 'ObjectBox':
        options = StoreOptions()
        try:
            if self._directory:
                options.directory(self._directory)
            if self._max_db_size_in_kb:
                options.max_db_size_in_kb(self._max_db_size_in_kb)
            options.model(self._model)
        except CoreException:
            options._free()
            raise
        c_store = obx_store_open(options._c_handle)
        return ObjectBox(c_store)
