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

"""ObjectBox Python API"""

from objectbox.store import Store
from objectbox.box import Box
from objectbox.model.entity import Entity, SyncEntity
from objectbox.model.properties import Id, String, Index, Bool, Int8, Int16, Int32, Int64, Float32, Float64, Bytes, BoolVector, Int8Vector, Int16Vector, Int32Vector, Int64Vector, Float32Vector, Float64Vector, CharVector, BoolList, Int8List, Int16List, Int32List, Int64List, Float32List, Float64List, CharList, Date, DateNano, Flex, Relation, IndexType, Unique, ConflictStrategy, HnswIndex, VectorDistanceType, HnswFlags, SyncClock, SyncPrecedence
from objectbox.model.model import Model
from objectbox.c import version_core, DebugFlags
# The exceptions most likely handled by applications (all are in objectbox.exceptions; its TimeoutError is not
# exported here, as it would shadow the built-in TimeoutError on "from objectbox import *")
from objectbox.exceptions import (DbError, IllegalArgumentError, IllegalStateError, UniqueViolatedError,
                                  ConstraintViolatedError, NonUniqueResultError, IdNotFoundError,
                                  FeatureNotAvailableError, SchemaError, DbFullError, MaxDataSizeExceededError,
                                  MaxReadersExceededError, StoreMustShutdownError, FileCorruptError,
                                  FilePagesCorruptError, NumericOverflowError)
from objectbox.version import Version
from objectbox.condition import PropertyQueryCondition
from objectbox.query import Query, ObjectWithScore, IdWithScore
from objectbox.query_builder import QueryBuilder
from objectbox.builder import Builder
from objectbox.objectbox import ObjectBox
from objectbox.query_builder import OrderFlags

__all__ = [
    'Box',
    'Builder',
    'Model',
    'Entity',
    'Id',
    'Bool',
    'Int8',
    'Int16',
    'Int32',
    'Int64',
    'Float32',
    'Float64',
    'Bytes',
    'String',
    'BoolVector',
    'Int8Vector',
    'Int16Vector',
    'Int32Vector',
    'Int64Vector',
    'Float32Vector',
    'Float64Vector',
    'CharVector',
    'BoolList',
    'Int8List',
    'Int16List',
    'Int32List',
    'Int64List',
    'Float32List',
    'Float64List',
    'CharList',
    'Date',
    'DateNano',
    'Flex',
    'Relation',
    'Index',
    'IndexType',
    'Unique',
    'ConflictStrategy',
    'HnswIndex',
    'VectorDistanceType',
    'Store',
    'ObjectBox',
    'DbError',
    'IllegalArgumentError',
    'IllegalStateError',
    'UniqueViolatedError',
    'ConstraintViolatedError',
    'NonUniqueResultError',
    'IdNotFoundError',
    'FeatureNotAvailableError',
    'SchemaError',
    'DbFullError',
    'MaxDataSizeExceededError',
    'MaxReadersExceededError',
    'StoreMustShutdownError',
    'FileCorruptError',
    'FilePagesCorruptError',
    'NumericOverflowError',
    'version',
    'version_info',
    'DebugFlags',
    'PropertyQueryCondition',
    'HnswFlags',
    'Query',
    'ObjectWithScore',
    'IdWithScore',
    'QueryBuilder',
    'SyncEntity',
    'SyncClock',
    'SyncPrecedence',
    'OrderFlags',
    # Sync (loaded on first use; see __getattr__)
    'Sync',
    'SyncClient',
    'SyncCredentials',
    'SyncState',
    'SyncRequestUpdatesMode',
    'SyncFlags',
    'SyncStats',
    'SyncCode',
    'SyncChange',
    'SyncListener',
    'SyncLoginListener',
    'SyncConnectionListener',
    'SyncCompletedListener',
    'SyncTimeListener',
    'SyncChangeListener',
]

_sync_names = frozenset(__all__[__all__.index('Sync'):])


def __getattr__(name: str):
    # Sync names are imported on first use: importing objectbox.sync takes a few milliseconds, also for apps without
    # Sync (a module __getattr__, PEP 562; also used by "from objectbox import *")
    if name in _sync_names:
        import objectbox.sync
        return getattr(objectbox.sync, name)
    raise AttributeError(f"module 'objectbox' has no attribute '{name}'")

# Python binding version
version = Version(5, 0, 0)
"""ObjectBox Python package version"""

def version_info():
    """Returns a string with Python and core version information."""
    return "ObjectBox Python version " + str(version) + " using dynamic library version " + str(version_core)
