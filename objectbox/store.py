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


import objectbox.c as c
import objectbox.transaction
from objectbox.store_options import StoreOptions
import objectbox
from objectbox.model.entity import _Entity
from typing import *

class Store:
    def __init__(self, 
                 model : Optional[objectbox.model.Model] = None, 
                 directory : Optional[str] = None, 
                 max_db_size_in_kb : Optional[int] = None,
                 max_data_size_in_kb: Optional[int] = None,
                 file_mode: Optional[int] = None,
                 max_readers: Optional[int] = None,
                 no_reader_thread_locals: Optional[bool] = None,
                 model_bytes: Optional[bytes] = None,
                 model_bytes_direct: Optional[bytes] = None,
                 read_schema: Optional[bool] = None,
                 use_previous_commit: Optional[bool] = None,
                 read_only: Optional[bool] = None,
                 debug_flags: Optional[c.DebugFlags] = None,
                 async_max_queue_length: Optional[int] = None,
                 async_throttle_at_queue_length: Optional[int] = None,
                 async_throttle_micros: Optional[int] = None,
                 async_max_in_tx_duration: Optional[int] = None,
                 async_max_in_tx_operations: Optional[int] = None,
                 async_pre_txn_delay: Optional[int] = None,
                 async_post_txn_delay: Optional[int] = None,
                 async_minor_refill_threshold: Optional[int] = None,
                 async_minor_refill_max_count: Optional[int] = None,
                 async_object_bytes_max_cache_size: Optional[int] = None,
                 async_object_bytes_max_size_to_cache: Optional[int] = None,
                 c_store : Optional[c.OBX_store_p] = None):
        
        """Opens an ObjectBox database Store

        :param model:
            Database schema model.
        :param directory:
            Store directory. Defaults to "objectbox". 
            Use prefix "memory:" to open an in-memory database, e.g. "memory:myapp"
        :param max_db_size_in_kb:
            Maximum database size. Defaults to one gigabyte.
        :param max_data_size_in_kb:
            Maximum data in database size tracking. Defaults to being disabled.
            This is a more involved size tacking.
            Recommended only if stricter accurate limit is required.
            Data size must be below database size. 
        :param file_mode:
            Unix-style file mode options. Defaults to "int('644',8)". 
            This option is ignored on Windows platforms.
        :param max_readers:
            Maximum number of readers (related to read transactions).
            Default value (currently 126) is suitable for most applications.
        :param no_reader_thread_locals:
            Disables the usage of thread locals for "readers" related to read transactions.
            This can make sense if you are using a lot of threads that are kept alive.
        :param model_bytes:
            Database schema model given by flatbuffers bytes serialized model. 
        :param model_bytes_direct:
            Database schema model given by flatbuffers bytes serialized model without copying.
        :param read_schema:
            Advanced settings.
        :param use_previous_commit:
            Advanced setting recommended to set with read_only to ensure no data is lost.
        :param read_only:
            Open store in read-only mode: no schema update, no write transactions. Defaults to false.
        :param debug_flags:
            Set debug flags. Defaults to DebugFlags.NONE.
        :param async_max_queue_length:
            Maximum size of the queue before new transactions will be rejected.
        :param async_throttle_at_queue_length:
            Throttle queue submitter when hitting this water mark.
        :param async_throttle_micros:
            Sleeping time for throttled queue submitter.
        :param async_max_in_tx_duration:
            Maximum duration spent in a transaction before queue enforces a commit.
        :param async_max_in_tx_operations:
            Maximum number of operations performed in a transaction before queye enforces a commit.
        :param async_pre_txn_delay:
            Delay (in micro seconds) before queue is triggered by new element.
        :param async_post_txn_delay:
            Delay (in micro seconds) after a transaction was committed.
        :param async_minor_refill_threshold:
            Number of operations to be considered a "minor refill". 
        :param async_minor_refill_max_count:
            If set, allows "minor refills" with small batches that came in (off by default).
        :param async_object_bytes_max_cache_size:
            Total cache size. Defaults to 0.5 mega bytes.
        :param async_object_bytes_max_size_to_cache:
            Maximum size for an object to be cached.
        :param c_store:
            Internal parameter for deprecated ObjectBox interface. Do not use it; other options would be ignored if passed.
        """ 
        
        self._c_store = None
        if not c_store:
            options = StoreOptions()
            try:
                if model is not None:
                    options.model(model)
                if directory is not None:
                    options.directory(directory)
                if max_db_size_in_kb is not None:
                    options.max_db_size_in_kb(max_db_size_in_kb)
                if max_data_size_in_kb is not None:
                    options.max_data_size_in_kb(max_data_size_in_kb)
                if file_mode is not None:
                    options.file_mode(file_mode)
                if max_readers is not None:
                    options.max_readers(max_readers)
                if no_reader_thread_locals is not None:
                    options.no_reader_thread_locals(no_reader_thread_locals)
                if model_bytes is not None:
                    options.model_bytes(model_bytes)
                if model_bytes_direct is not None:
                    options.model_bytes_direct(model_bytes_direct)
                if read_schema is not None:
                    options.read_schema(read_schema)
                if use_previous_commit is not None:
                    options.use_previous_commit(use_previous_commit)
                if read_only is not None:
                    options.read_only(read_only)
                if debug_flags is not None:
                    options.debug_flags(debug_flags)
                if async_max_queue_length is not None:
                    options.async_max_queue_length(async_max_queue_length)
                if async_throttle_at_queue_length is not None:
                    options.async_throttle_at_queue_length(async_throttle_at_queue_length)
                if async_throttle_micros is not None:
                    options.async_throttle_micros(async_throttle_micros)
                if async_max_in_tx_duration is not None:
                    options.async_max_in_tx_duration(async_max_in_tx_duration)
                if async_max_in_tx_operations is not None:
                    options.async_max_in_tx_operations(async_max_in_tx_operations)
                if async_pre_txn_delay is not None:
                    options.async_pre_txn_delay(async_pre_txn_delay)
                if async_post_txn_delay is not None:
                    options.async_post_txn_delay(async_post_txn_delay)
                if async_minor_refill_threshold is not None:
                    options.async_minor_refill_threshold(async_minor_refill_threshold)
                if async_minor_refill_max_count is not None:
                    options.async_minor_refill_max_count(async_minor_refill_max_count)
                if async_object_bytes_max_cache_size is not None:
                    options.async_object_bytes_max_cache_size(async_object_bytes_max_cache_size)
                if async_object_bytes_max_size_to_cache is not None:
                    options.async_object_bytes_max_size_to_cache(async_object_bytes_max_size_to_cache)    
                
            except c.CoreException:
                options._free()
                raise
            self._c_store = c.obx_store_open(options._c_handle)                 
        else:
            self._c_store = c_store

    def __del__(self):
        self.close()
    
    def box(self, entity: _Entity) -> 'objectbox.Box':
        """
        Open a box for an entity.
        
        :param entity:
            Entity type of the model
        """
        return objectbox.Box(self, entity)

    def read_tx(self):
        return objectbox.transaction.read(self)

    def write_tx(self):
        return objectbox.transaction.write(self)

    def close(self):
        c_store_to_close = self._c_store
        if c_store_to_close:
            self._c_store = None
            c.obx_store_close(c_store_to_close)

    def remove_db_files(dir):
        """
        Remove Database files
        
        :param dir:
            Path to directory.
        """
        c.obx_remove_db_files(c.c_str(dir))
