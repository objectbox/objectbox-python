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
import objectbox.transaction


class ObjectBox:
    def __init__(self, c_store: OBX_store_p):
        self._c_store = c_store

    def __del__(self):
        obx_store_close(self._c_store)

    def read_tx(self):
        return objectbox.transaction.read(self)

    def write_tx(self):
        return objectbox.transaction.write(self)
