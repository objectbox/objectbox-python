from objectbox.c import *
from objectbox.model import Model


class StoreOptions:
    """ A RAII wrapper to the C API for setting the store options. """

    _c_handle: Optional[int]

    def __init__(self):
        self._c_handle = obx_opt()

    def _free(self):
        if self._c_handle is not None:
            obx_opt_free(self._c_handle)
            self._c_handle = None

    def directory(self, path: str):
        obx_opt_directory(self._c_handle, c_str(path))

    def max_db_size_in_kb(self, size_in_kb: int):
        obx_opt_max_db_size_in_kb(self._c_handle, size_in_kb)

    def max_data_size_in_kb(self, size_in_kb: int):
        obx_opt_max_data_size_in_kb(self._c_handle, size_in_kb)

    def file_mode(self, file_mode: int):
        obx_opt_file_mode(self._c_handle, file_mode)

    def max_readers(self, max_readers: int):
        obx_opt_max_readers(self._c_handle, max_readers)

    def no_reader_thread_locals(self, flag: bool):
        obx_opt_no_reader_thread_locals(self._c_handle, flag)

    def model(self, model: Model):
        model._finish()
        obx_opt_model(self._c_handle, model._c_model)

    def model_bytes(self, bytes_: bytes):
        obx_opt_model_bytes(self._c_handle, len(bytes_))

    def model_bytes_direct(self, bytes_: bytes):
        obx_opt_model_bytes_direct(self._c_handle, len(bytes_))

    def validate_on_open_pages(self, page_limit: int, flags: int):
        raise NotImplementedError  # TODO

    def validate_on_open_kv(self, flags: OBXValidateOnOpenKvFlags):
        raise NotImplementedError  # TODO

    def put_padding_mode(self, mode: OBXPutPaddingMode):
        obx_opt_put_padding_mode(self._c_handle, mode)

    def read_schema(self, value: bool):
        obx_opt_read_schema(self._c_handle, value)

    def use_previous_commit(self, value: bool):
        obx_opt_use_previous_commit(self._c_handle, value)

    def read_only(self, value: bool):
        obx_opt_read_only(self._c_handle, value)

    def debug_flags(self, flags: OBXDebugFlags):
        obx_opt_debug_flags(self._c_handle, flags)

    def add_debug_flags(self, flags: OBXDebugFlags):
        obx_opt_add_debug_flags(self._c_handle, flags)

    def async_max_queue_length(self, value: int):
        obx_opt_async_max_queue_length(self._c_handle, value)

    def async_throttle_at_queue_length(self, value: int):
        obx_opt_async_throttle_at_queue_length(self._c_handle, value)

    def async_throttle_micros(self, value: int):
        obx_opt_async_throttle_micros(self._c_handle, value)

    def async_max_in_tx_duration(self, micros: int):
        obx_opt_async_max_in_tx_duration(self._c_handle, micros)

    def async_max_in_tx_operations(self, value: int):
        obx_opt_async_max_in_tx_operations(self._c_handle, value)

    def async_pre_txn_delay(self, delay_micros: int):
        obx_opt_async_pre_txn_delay(self._c_handle, delay_micros)

    def async_pre_txn_delay4(self, delay_micros: int, delay2_micros: int, min_queue_length_for_delay2: int):
        obx_opt_async_pre_txn_delay4(self._c_handle, delay_micros, delay2_micros, min_queue_length_for_delay2)

    def async_post_txn_delay(self, delay_micros: int):
        obx_opt_async_post_txn_delay(self._c_handle, delay_micros)

    def async_post_txn_delay5(self, delay_micros: int, delay2_micros: int, min_queue_length_for_delay2: int,
                              subtract_processing_time: bool):
        obx_opt_async_post_txn_delay5(self._c_handle, delay_micros, delay2_micros, min_queue_length_for_delay2,
                                      subtract_processing_time)

    def async_minor_refill_threshold(self, queue_length: int):
        obx_opt_async_minor_refill_threshold(self._c_handle, queue_length)

    def async_minor_refill_max_count(self, value: int):
        obx_opt_async_minor_refill_max_count(self._c_handle, value)

    def async_max_tx_pool_size(self, value: int):
        obx_opt_async_max_tx_pool_size(self._c_handle, value)

    def async_object_bytes_max_cache_size(self, value: int):
        obx_opt_async_object_bytes_max_cache_size(self._c_handle, value)

    def async_object_bytes_max_size_to_cache(self, value: int):
        obx_opt_async_object_bytes_max_size_to_cache(self._c_handle, value)

    # TODO def log_callback(self):

    def backup_restore(self, backup_file: str, flags: OBXBackupRestoreFlags):
        raise NotImplementedError  # TODO

    def get_directory(self) -> str:
        dir_bytes = obx_opt_get_directory(self._c_handle)
        return dir_bytes.decode('utf-8')

    def get_max_db_size_in_kb(self) -> int:
        return obx_opt_get_max_db_size_in_kb(self._c_handle)

    def get_max_data_size_in_kb(self) -> int:
        return obx_opt_get_max_data_size_in_kb(self._c_handle)

    def get_debug_flags(self) -> OBXDebugFlags:
        return obx_opt_get_debug_flags(self._c_handle)
