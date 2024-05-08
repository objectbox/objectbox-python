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
from objectbox.model import Model
from objectbox.store import Store
from objectbox.store_options import StoreOptions
from warnings import warn

class Builder:
    def __init__(self):
        """This throws a deprecation warning on initialization."""
        warn(f'Using {self.__class__.__name__} is deprecated, please use Store(model=, directory= ...) from objectbox.store.', DeprecationWarning, stacklevel=2)
        self._kwargs = { }

    def directory(self, path: str) -> 'Builder':
        self._kwargs['directory'] = path
        return self

    def max_db_size_in_kb(self, size_in_kb: int) -> 'Builder':
        self._kwargs['max_db_size_in_kb'] = size_in_kb
        return self

    def model(self, model: Model) -> 'Builder':
        self._kwargs['model'] = model
        return self

    def build(self) -> 'Store':
        return Store(**self._kwargs)