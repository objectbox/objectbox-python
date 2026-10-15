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


# Context managers as classes, not via @contextmanager: ~0.7 µs less overhead per transaction.

class _ReadTx:
    __slots__ = ('_c_store', '_tx')

    def __init__(self, store: 'Store'):
        self._c_store = store._c_store

    def __enter__(self):
        self._tx = obx_txn_read(self._c_store)

    def __exit__(self, exc_type, exc_value, traceback):
        obx_txn_close(self._tx)


class _WriteTx:
    __slots__ = ('_c_store', '_tx')

    def __init__(self, store: 'Store'):
        self._c_store = store._c_store

    def __enter__(self):
        self._tx = obx_txn_write(self._c_store)

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is not None:
            obx_txn_close(self._tx)  # abort
            return
        try:
            obx_txn_success(self._tx)  # commit and close
        except BaseException:
            obx_txn_close(self._tx)
            raise


def read(store: 'Store') -> _ReadTx:
    """Returns a context manager for a read transaction."""
    return _ReadTx(store)


def write(store: 'Store') -> _WriteTx:
    """Returns a context manager for a write transaction; committed unless an exception is raised."""
    return _WriteTx(store)
