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


import objectbox.store
from warnings import warn

class ObjectBox(objectbox.store.Store):
    def __init__(self, c_store):
        """This throws a deprecation warning on initialization."""
        warn(f'{self.__class__.__name__} will be deprecated, use Store from objectbox.store.', DeprecationWarning, stacklevel=2)
        super().__init__(c_store=c_store)
