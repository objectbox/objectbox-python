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


class Builder:
    def __init__(self):
        self._model = Model()
        self._directory = ''

    def directory(self, path: str) -> 'Builder':
        self._directory = path
        return self

    def model(self, model: Model) -> 'Builder':
        self._model = model
        self._model._finish()
        return self

    def build(self) -> 'ObjectBox':
        c_options = obx_opt()

        try:
            if len(self._directory) > 0:
                obx_opt_directory(c_options, c_str(self._directory))

            obx_opt_model(c_options, self._model._c_model)
        except CoreException:
            obx_opt_free(c_options)
            raise

        c_store = obx_store_open(c_options)
        return ObjectBox(c_store)
