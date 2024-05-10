from objectbox.c import *  # TODO ideally we wouldn't have to import c.py
from objectbox.store_options import StoreOptions
import objectbox
import tests.common

def test_set_options():
    """ Test setting dummy values for each option.
    Checks that Python types are correctly forwarded to C API. """

    options = StoreOptions()
    options.directory("test-db")
    options.max_db_size_in_kb(8192)
    options.max_data_size_in_kb(4096)
    options.file_mode(755)
    options.max_readers(10)
    options.no_reader_thread_locals(False)
    # options.model
    # options.model_bytes
    # options.model_bytes_direct
    # options.validate_on_open_pages
    # options.validate_on_open_kv
    options.put_padding_mode(OBXPutPaddingMode_PaddingAutomatic)
    options.read_schema(False)
    options.use_previous_commit(False)
    options.read_only(True)
    options.debug_flags(OBXDebugFlags_LOG_TRANSACTIONS_READ)
    options.add_debug_flags(OBXDebugFlags_LOG_CACHE_HITS)
    options.async_max_queue_length(100)
    options.async_throttle_at_queue_length(1024)
    options.async_throttle_micros(1000)
    options.async_max_in_tx_duration(1000)
    options.async_max_in_tx_operations(20)
    options.async_pre_txn_delay(500)
    options.async_pre_txn_delay4(500, 700, 100)
    options.async_post_txn_delay(500)
    options.async_post_txn_delay5(500, 700, 100, False)
    options.async_minor_refill_threshold(100)
    options.async_minor_refill_max_count(500)
    options.async_max_tx_pool_size(100)
    options.async_object_bytes_max_cache_size(4096)
    options.async_object_bytes_max_size_to_cache(4096)
    # options.log_callback
    # options.backup_restore

    assert options.get_directory() == "test-db"
    assert options.get_max_db_size_in_kb() == 8192
    assert options.get_max_data_size_in_kb() == 4096
    assert options.get_debug_flags() == (OBXDebugFlags_LOG_TRANSACTIONS_READ | OBXDebugFlags_LOG_CACHE_HITS)

    del options

def test_store_with_options():
    store = objectbox.Store(
        model=tests.common.create_default_model(),
        directory=tests.common.test_dir,
        max_db_size_in_kb=1<<30,
        max_data_size_in_kb=(1<<30)-(1<<20),
        file_mode=int('664',8),
        max_readers=126,
        no_reader_thread_locals=True,
        read_schema=True,
        use_previous_commit=False,
        read_only=False,
        debug_flags=DebugFlags.LOG_TRANSACTIONS_READ|DebugFlags.LOG_TRANSACTIONS_WRITE,
        async_max_queue_length=100,
        async_throttle_at_queue_length=100,
        async_throttle_micros=50000,
        async_max_in_tx_duration=50000,
        async_max_in_tx_operations=1000,
        async_pre_txn_delay=100000,
        async_post_txn_delay=100000,
        async_minor_refill_threshold=10,
        async_minor_refill_max_count=100,
        async_object_bytes_max_cache_size=1<<20,
        async_object_bytes_max_size_to_cache=100<<10
    ) 
    del store
