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


import ctypes.util
import os
import platform
from ctypes import c_char_p
from typing import *

import numpy as np

from objectbox.version import Version

# This file contains C-API bindings based on lib/objectbox.h, linking to the 'objectbox' shared library.
# The bindings are implementing using ctypes, see https://docs.python.org/dev/library/ctypes.html for introduction.


# Version of the library used by the binding. This version is checked at runtime to ensure binary compatibility.
# Don't forget to update download-c-lib.py when upgrading to a newer version.
required_version = "5.0.0"


def shlib_name(library: str) -> str:
    """Returns the platform-specific name of the shared library"""
    if platform.system() == 'Linux':
        return 'lib' + library + '.so'
    elif platform.system() == 'Windows':
        return library + '.dll'
    elif platform.system() == 'Darwin':
        return 'lib' + library + '.dylib'
    else:
        assert False, 'Unsupported platform: ' + platform.system()


# initialize the C library
lib_path = os.path.dirname(os.path.realpath(__file__))
lib_path = os.path.join(lib_path, 'lib',
                        platform.machine() if platform.system() != 'Darwin' else 'macos-universal',
                        shlib_name('objectbox'))
C = ctypes.CDLL(lib_path)

# load the core library version
__major = ctypes.c_int(0)
__minor = ctypes.c_int(0)
__patch = ctypes.c_int(0)
C.obx_version(ctypes.byref(__major), ctypes.byref(
    __minor), ctypes.byref(__patch))

# C-api (core library) version
version_core = Version(__major.value, __minor.value, __patch.value)

assert str(version_core) == required_version, \
    "Incorrect ObjectBox version loaded: %s instead of expected %s " % (
        str(version_core), required_version)

# define some basic types
obx_err = ctypes.c_int
obx_schema_id = ctypes.c_uint32
obx_uid = ctypes.c_uint64
obx_id = ctypes.c_uint64
obx_qb_cond = ctypes.c_int

obx_qb_cond_p = ctypes.POINTER(obx_qb_cond)

# enums
OBXPropertyType = ctypes.c_int
OBXPropertyFlags = ctypes.c_int
OBXDebugFlags = ctypes.c_int
OBXPutMode = ctypes.c_int
OBXPutPaddingMode = ctypes.c_int
OBXOrderFlags = ctypes.c_int
OBXHnswFlags = ctypes.c_int
OBXVectorDistanceType = ctypes.c_int
OBXValidateOnOpenPagesFlags = ctypes.c_int
OBXValidateOnOpenKvFlags = ctypes.c_int
OBXBackupRestoreFlags = ctypes.c_int
OBXLogLevel = ctypes.c_int

from enum import IntEnum
class LogLevel(IntEnum):
    Verbose = 10
    Debug   = 20
    Info    = 30
    Warn    = 40
    Error   = 50


class DebugFlags(IntEnum):
    """Debug flags"""

    NONE = 0,

    LOG_TRANSACTIONS_READ = 1,
    """ Log read transactions """

    LOG_TRANSACTIONS_WRITE = 2,
    """ Log write transactions """

    LOG_QUERIES = 3,
    """ Log queries """

    LOG_QUERY_PARAMETERS = 8,
    """ Log query parameters """

    LOG_ASYNC_QUEUE = 16,
    """ Log async queue """

    LOG_CACHE_HITS = 32,
    """ Log cache hits """

    LOG_CACHE_ALL = 64,
    """ Log cache hits """

    LOG_TREE = 128
    """ Log tree operations """


class OBX_model(ctypes.Structure):
    pass


OBX_model_p = ctypes.POINTER(OBX_model)


class OBX_store(ctypes.Structure):
    pass


OBX_store_p = ctypes.POINTER(OBX_store)


class OBX_store_options(ctypes.Structure):
    pass


OBX_store_options_p = ctypes.POINTER(OBX_store_options)


class OBX_bytes(ctypes.Structure):
    _fields_ = [
        ('data', ctypes.c_void_p),
        ('size', ctypes.c_size_t),
    ]


OBX_bytes_p = ctypes.POINTER(OBX_bytes)


class OBX_bytes_array(ctypes.Structure):
    _fields_ = [
        ('data', OBX_bytes_p),
        ('count', ctypes.c_size_t),
    ]


OBX_bytes_array_p = ctypes.POINTER(OBX_bytes_array)


class OBX_bytes_score(ctypes.Structure):
    _fields_ = [
        ('data', ctypes.c_void_p),
        ('size', ctypes.c_size_t),
        ('score', ctypes.c_double),
    ]


OBX_bytes_score_p = ctypes.POINTER(OBX_bytes_score)


class OBX_bytes_score_array(ctypes.Structure):
    _fields_ = [
        ('bytes_scores', OBX_bytes_score_p),
        ('count', ctypes.c_size_t),
    ]


OBX_bytes_score_array_p = ctypes.POINTER(OBX_bytes_score_array)


class OBX_id_array(ctypes.Structure):
    _fields_ = [
        ('ids', ctypes.POINTER(obx_id)),
        ('count', ctypes.c_size_t),
    ]


OBX_id_array_p = ctypes.POINTER(OBX_id_array)


class OBX_id_score(ctypes.Structure):
    _fields_ = [
        ('id', obx_id),
        ('score', ctypes.c_double)
    ]


OBX_id_score_p = ctypes.POINTER(OBX_id_score)


class OBX_id_score_array(ctypes.Structure):
    _fields_ = [
        ('ids_scores', OBX_id_score_p),
        ('count', ctypes.c_size_t)
    ]


OBX_id_score_array_p = ctypes.POINTER(OBX_id_score_array)


class OBX_txn(ctypes.Structure):
    pass


OBX_txn_p = ctypes.POINTER(OBX_txn)


class OBX_box(ctypes.Structure):
    pass


OBX_box_p = ctypes.POINTER(OBX_box)


class OBX_async(ctypes.Structure):
    pass


OBX_async_p = ctypes.POINTER(OBX_async)


class OBX_query_builder(ctypes.Structure):
    pass


OBX_query_builder_p = ctypes.POINTER(OBX_query_builder)


class OBX_query(ctypes.Structure):
    pass


OBX_query_p = ctypes.POINTER(OBX_query)

# manually configure error methods, we can't use `fn()` defined below yet due to circular dependencies
C.obx_last_error_message.restype = ctypes.c_char_p
C.obx_last_error_code.restype = obx_err


class DbErrorCode(IntEnum):
    OBX_SUCCESS = 0
    OBX_NOT_FOUND = 404
    OBX_NO_SUCCESS = 1001
    OBX_TIMEOUT = 1002
    OBX_ERROR_ILLEGAL_STATE = 10001
    OBX_ERROR_ILLEGAL_ARGUMENT = 10002
    OBX_ERROR_ALLOCATION = 10003
    OBX_ERROR_NUMERIC_OVERFLOW = 10004
    OBX_ERROR_FEATURE_NOT_AVAILABLE = 10005
    OBX_ERROR_SHUTTING_DOWN = 10006
    OBX_ERROR_IO = 10007
    OBX_ERROR_BACKUP_FILE_INVALID = 10008
    OBX_ERROR_NO_ERROR_INFO = 10097
    OBX_ERROR_GENERAL = 10098
    OBX_ERROR_UNKNOWN = 10099
    OBX_ERROR_DB_FULL = 10101
    OBX_ERROR_MAX_READERS_EXCEEDED = 10102
    OBX_ERROR_STORE_MUST_SHUTDOWN = 10103
    OBX_ERROR_MAX_DATA_SIZE_EXCEEDED = 10104
    OBX_ERROR_DB_GENERAL = 10198
    OBX_ERROR_STORAGE_GENERAL = 10199
    OBX_ERROR_UNIQUE_VIOLATED = 10201
    OBX_ERROR_NON_UNIQUE_RESULT = 10202
    OBX_ERROR_PROPERTY_TYPE_MISMATCH = 10203
    OBX_ERROR_ID_ALREADY_EXISTS = 10210
    OBX_ERROR_ID_NOT_FOUND = 10211
    OBX_ERROR_TIME_SERIES = 10212
    OBX_ERROR_CONSTRAINT_VIOLATED = 10299
    OBX_ERROR_STD_ILLEGAL_ARGUMENT = 10301
    OBX_ERROR_STD_OUT_OF_RANGE = 10302
    OBX_ERROR_STD_LENGTH = 10303
    OBX_ERROR_STD_BAD_ALLOC = 10304
    OBX_ERROR_STD_RANGE = 10305
    OBX_ERROR_STD_OVERFLOW = 10306
    OBX_ERROR_STD_OTHER = 10399
    OBX_ERROR_SCHEMA = 10501
    OBX_ERROR_FILE_CORRUPT = 10502
    OBX_ERROR_FILE_PAGES_CORRUPT = 10503
    OBX_ERROR_SCHEMA_OBJECT_NOT_FOUND = 10504
    OBX_ERROR_TREE_MODEL_INVALID = 10601
    OBX_ERROR_TREE_VALUE_TYPE_MISMATCH = 10602
    OBX_ERROR_TREE_PATH_NON_UNIQUE = 10603
    OBX_ERROR_TREE_PATH_ILLEGAL = 10604
    OBX_ERROR_TREE_OTHER = 10699


class OBXEntityFlags(IntEnum):
    SYNC_ENABLED = 2
    SHARED_GLOBAL_IDS = 4


def check_obx_err(code: obx_err, func, args) -> obx_err:
    """ Raises an exception if obx_err is not successful. """
    if code != DbErrorCode.OBX_SUCCESS:
        from objectbox.exceptions import create_db_error
        raise create_db_error(code)
    return code

def check_obx_success(code: obx_err) -> bool:
    if code == DbErrorCode.OBX_NO_SUCCESS:
        return False
    check_obx_err(code, None, None)
    return True

def check_obx_qb_cond(qb_cond: obx_qb_cond, func, args) -> obx_qb_cond:
    """ Raises an exception if obx_qb_cond is not successful. """
    if qb_cond == 0:
        from objectbox.exceptions import create_db_error
        raise create_db_error(C.obx_last_error_code())
    return qb_cond


# assert that the returned pointer/int is non-empty
def check_result(result, func, args):
    if not result:
        from objectbox.exceptions import create_db_error
        raise create_db_error(C.obx_last_error_code())
    return result


# creates a global function "name" with the given restype & argtypes, calling C function with the same name.
# restype is used for error checking: if not None, check_result will throw an exception if the result is empty.
def c_fn(name: str, restype: Optional[type], argtypes):
    func = C.__getattr__(name)
    func.argtypes = argtypes
    func.restype = restype

    if restype is not None:
        func.errcheck = check_result

    return func


# creates a global function "name" with the given restype & argtypes, calling C function with the same name.
# no error checking is done on restype as this is defered to higher-level functions.
def c_fn_nocheck(name: str, restype: type, argtypes):
    func = C.__getattr__(name)
    func.argtypes = argtypes
    func.restype = restype
    return func


# like c_fn, but for functions returning obx_err
def c_fn_rc(name: str, argtypes):
    """ Like c_fn, but for functions returning obx_err (checks obx_err validity). """
    func = C.__getattr__(name)
    func.argtypes = argtypes
    func.restype = obx_err
    func.errcheck = check_obx_err
    return func


def c_fn_qb_cond(name: str, argtypes):
    """ Like c_fn, but for functions returning obx_qb_cond (checks obx_qb_cond validity). """
    func = C.__getattr__(name)
    func.argtypes = argtypes
    func.restype = obx_qb_cond
    func.errcheck = check_obx_qb_cond
    return func


def py_str(ptr: ctypes.c_char_p) -> str:
    return ctypes.c_char_p(ptr).value.decode("utf-8")


def c_str(string: str) -> ctypes.c_char_p:
    return string.encode('utf-8')


def c_voidp_as_bytes(voidp, size):
    # TODO verify which of the following two approaches is better. Performance-wise, it seems the same.

    # slice the data from the pointer
    # return ctypes.cast(voidp, ctypes.POINTER(ctypes.c_char))[:size]

    # create a memory view
    return memoryview(ctypes.cast(voidp, ctypes.POINTER(ctypes.c_ubyte * size))[0]).tobytes()


def c_array(py_list: Union[List[Any], np.ndarray], c_type):
    """ Converts the given python list or ndarray into a C array of c_type. """
    if isinstance(py_list, np.ndarray):
        if py_list.ndim != 1:
            raise Exception(f"ndarray is expected to be 1-dimensional. Input shape: {py_list.shape}")
        return py_list.ctypes.data_as(ctypes.POINTER(c_type))
    elif isinstance(py_list, list):
        return (c_type * len(py_list))(*py_list)
    else:
        raise Exception(f"Unsupported Python list type: {type(py_list)}")


def c_array_pointer(py_list: Union[List[Any], np.ndarray], c_type):
    """ Converts the given python list or ndarray into a C array of c_type. Returns its pointer type. """
    return ctypes.cast(c_array(py_list, c_type), ctypes.POINTER(c_type))


# OBX_C_API float obx_vector_distance_float32(OBXVectorDistanceType type, const float* vector1, const float* vector2, size_t dimension);
obx_vector_distance_float32 = c_fn("obx_vector_distance_float32", ctypes.c_float,
                                   [OBXVectorDistanceType, ctypes.POINTER(ctypes.c_float),
                                    ctypes.POINTER(ctypes.c_float), ctypes.c_size_t])

# OBX_C_API float obx_vector_distance_to_relevance(OBXVectorDistanceType type, float distance);
obx_vector_distance_to_relevance = c_fn("obx_vector_distance_to_relevance", ctypes.c_float,
                                        [OBXVectorDistanceType, ctypes.c_float])

# OBX_model* (void);
obx_model = c_fn('obx_model', OBX_model_p, [])

# obx_err (OBX_model* model, const char* name, obx_schema_id entity_id, obx_uid entity_uid);
obx_model_entity = c_fn_rc('obx_model_entity', [
    OBX_model_p, ctypes.c_char_p, obx_schema_id, obx_uid])

# obx_err obx_model_entity_flags(OBX_model* model, uint32_t flags);
obx_model_entity_flags = c_fn_rc('obx_model_entity_flags', [OBX_model_p, ctypes.c_uint32])

# obx_err (OBX_model* model, const char* name, OBXPropertyType type, obx_schema_id property_id, obx_uid property_uid);
obx_model_property = c_fn_rc('obx_model_property',
                             [OBX_model_p, ctypes.c_char_p, OBXPropertyType, obx_schema_id, obx_uid])

# obx_err (OBX_model* model, OBXPropertyFlags flags);
obx_model_property_flags = c_fn_rc('obx_model_property_flags', [OBX_model_p, OBXPropertyFlags])

# obx_err obx_model_property_index_id(OBX_model* model, obx_schema_id index_id, obx_uid index_uid)
obx_model_property_index_id = c_fn_rc('obx_model_property_index_id', [OBX_model_p, obx_schema_id, obx_uid])

# obx_err obx_model_property_index_hnsw_dimensions(OBX_model* model, size_t value)
obx_model_property_index_hnsw_dimensions = \
    c_fn_rc('obx_model_property_index_hnsw_dimensions', [OBX_model_p, ctypes.c_size_t])

# obx_err obx_model_property_index_hnsw_neighbors_per_node(OBX_model* model, uint32_t value)
obx_model_property_index_hnsw_neighbors_per_node = \
    c_fn_rc('obx_model_property_index_hnsw_neighbors_per_node', [OBX_model_p, ctypes.c_uint32])

# obx_err obx_model_property_index_hnsw_indexing_search_count(OBX_model* model, uint32_t value)
obx_model_property_index_hnsw_indexing_search_count = \
    c_fn_rc('obx_model_property_index_hnsw_indexing_search_count', [OBX_model_p, ctypes.c_uint32])

# obx_err obx_model_property_index_hnsw_flags(OBX_model* model, OBXHnswFlags value)
obx_model_property_index_hnsw_flags = \
    c_fn_rc('obx_model_property_index_hnsw_flags', [OBX_model_p, OBXHnswFlags])

# obx_err obx_model_property_index_hnsw_distance_type(OBX_model* model, OBXVectorDistanceType value)
obx_model_property_index_hnsw_distance_type = c_fn_rc('obx_model_property_index_hnsw_distance_type',
                                                      [OBX_model_p, OBXVectorDistanceType])

# obx_err obx_model_property_index_hnsw_reparation_backlink_probability(OBX_model* model, float value)
obx_model_property_index_hnsw_reparation_backlink_probability = \
    c_fn_rc('obx_model_property_index_hnsw_reparation_backlink_probability', [OBX_model_p, ctypes.c_float])

# obx_err obx_model_property_index_hnsw_vector_cache_hint_size_kb(OBX_model* model, size_t value)
obx_model_property_index_hnsw_vector_cache_hint_size_kb = \
    c_fn_rc('obx_model_property_index_hnsw_vector_cache_hint_size_kb', [OBX_model_p, ctypes.c_size_t])

# obx_err (OBX_model*, obx_schema_id entity_id, obx_uid entity_uid);
obx_model_last_entity_id = c_fn('obx_model_last_entity_id', None, [
    OBX_model_p, obx_schema_id, obx_uid])

# obx_err (OBX_model* model, obx_schema_id index_id, obx_uid index_uid);
obx_model_last_index_id = c_fn('obx_model_last_index_id', None, [
    OBX_model_p, obx_schema_id, obx_uid])

# obx_err (OBX_model* model, obx_schema_id relation_id, obx_uid relation_uid);
obx_model_last_relation_id = c_fn('obx_model_last_relation_id', None, [
    OBX_model_p, obx_schema_id, obx_uid])

# obx_err (OBX_model* model, obx_schema_id property_id, obx_uid property_uid);
obx_model_entity_last_property_id = c_fn_rc('obx_model_entity_last_property_id',
                                            [OBX_model_p, obx_schema_id, obx_uid])

# OBX_store_options* ();
obx_opt = c_fn('obx_opt', OBX_store_options_p, [])

# OBX_C_API obx_err obx_opt_directory(OBX_store_options* opt, const char* dir);
obx_opt_directory = c_fn_rc('obx_opt_directory', [OBX_store_options_p, ctypes.c_char_p])

# OBX_C_API void obx_opt_max_db_size_in_kb(OBX_store_options* opt, uint64_t size_in_kb);
obx_opt_max_db_size_in_kb = c_fn('obx_opt_max_db_size_in_kb', None, [OBX_store_options_p, ctypes.c_uint64])

# OBX_C_API void obx_opt_max_data_size_in_kb(OBX_store_options* opt, uint64_t size_in_kb);
obx_opt_max_data_size_in_kb = c_fn('obx_opt_max_data_size_in_kb', None, [OBX_store_options_p, ctypes.c_uint64])

# OBX_C_API void obx_opt_file_mode(OBX_store_options* opt, unsigned int file_mode);
obx_opt_file_mode = c_fn('obx_opt_file_mode', None, [OBX_store_options_p, ctypes.c_uint32])

# OBX_C_API void obx_opt_max_readers(OBX_store_options* opt, unsigned int max_readers);
obx_opt_max_readers = c_fn('obx_opt_max_readers', None, [OBX_store_options_p, ctypes.c_uint32])

# OBX_C_API void obx_opt_no_reader_thread_locals(OBX_store_options* opt, bool flag);
obx_opt_no_reader_thread_locals = c_fn('obx_opt_no_reader_thread_locals', None, [OBX_store_options_p, ctypes.c_bool])

# OBX_C_API obx_err obx_opt_model(OBX_store_options* opt, OBX_model* model);
obx_opt_model = c_fn_rc('obx_opt_model', [OBX_store_options_p, OBX_model_p])

# OBX_C_API obx_err obx_opt_model_bytes(OBX_store_options* opt, const void* bytes, size_t size);
obx_opt_model_bytes = c_fn_rc('obx_opt_model_bytes', [OBX_store_options_p, ctypes.c_void_p, ctypes.c_size_t])

# OBX_C_API obx_err obx_opt_model_bytes_direct(OBX_store_options* opt, const void* bytes, size_t size);
obx_opt_model_bytes_direct = c_fn_rc('obx_opt_model_bytes_direct',
                                     [OBX_store_options_p, ctypes.c_void_p, ctypes.c_size_t])

# OBX_C_API void obx_opt_validate_on_open_pages(OBX_store_options* opt, size_t page_limit, uint32_t flags);
obx_opt_validate_on_open_pages = c_fn('obx_opt_validate_on_open_pages', None,
                                      [OBX_store_options_p, ctypes.c_size_t, OBXValidateOnOpenPagesFlags])

# OBX_C_API void obx_opt_validate_on_open_kv(OBX_store_options* opt, uint32_t flags);
obx_opt_validate_on_open_kv = c_fn('obx_opt_validate_on_open_kv', None, [OBX_store_options_p, OBXValidateOnOpenKvFlags])

# OBX_C_API void obx_opt_put_padding_mode(OBX_store_options* opt, OBXPutPaddingMode mode);
obx_opt_put_padding_mode = c_fn('obx_opt_put_padding_mode', None, [OBX_store_options_p, OBXPutPaddingMode])

# OBX_C_API void obx_opt_read_schema(OBX_store_options* opt, bool value);
obx_opt_read_schema = c_fn('obx_opt_read_schema', None, [OBX_store_options_p, ctypes.c_bool])

# OBX_C_API void obx_opt_use_previous_commit(OBX_store_options* opt, bool value);
obx_opt_use_previous_commit = c_fn('obx_opt_use_previous_commit', None, [OBX_store_options_p, ctypes.c_bool])

# OBX_C_API void obx_opt_read_only(OBX_store_options* opt, bool value);
obx_opt_read_only = c_fn('obx_opt_read_only', None, [OBX_store_options_p, ctypes.c_bool])

# OBX_C_API void obx_opt_debug_flags(OBX_store_options* opt, uint32_t flags);
obx_opt_debug_flags = c_fn('obx_opt_debug_flags', None, [OBX_store_options_p, OBXDebugFlags])

# OBX_C_API void obx_opt_add_debug_flags(OBX_store_options* opt, uint32_t flags);
obx_opt_add_debug_flags = c_fn('obx_opt_add_debug_flags', None, [OBX_store_options_p, ctypes.c_uint32])

# OBX_C_API void obx_opt_async_max_queue_length(OBX_store_options* opt, size_t value);
obx_opt_async_max_queue_length = c_fn('obx_opt_async_max_queue_length', None, [OBX_store_options_p, ctypes.c_size_t])

# OBX_C_API void obx_opt_async_throttle_at_queue_length(OBX_store_options* opt, size_t value);
obx_opt_async_throttle_at_queue_length = c_fn('obx_opt_async_throttle_at_queue_length', None,
                                              [OBX_store_options_p, ctypes.c_size_t])

# OBX_C_API void obx_opt_async_throttle_micros(OBX_store_options* opt, uint32_t value);
obx_opt_async_throttle_micros = c_fn('obx_opt_async_throttle_micros', None, [OBX_store_options_p, ctypes.c_uint32])

# OBX_C_API void obx_opt_async_max_in_tx_duration(OBX_store_options* opt, uint32_t micros);
obx_opt_async_max_in_tx_duration = c_fn('obx_opt_async_max_in_tx_duration', None,
                                        [OBX_store_options_p, ctypes.c_uint32])

# OBX_C_API void obx_opt_async_max_in_tx_operations(OBX_store_options* opt, uint32_t value);
obx_opt_async_max_in_tx_operations = c_fn('obx_opt_async_max_in_tx_operations', None,
                                          [OBX_store_options_p, ctypes.c_uint32])

# OBX_C_API void obx_opt_async_pre_txn_delay(OBX_store_options* opt, uint32_t delay_micros);
obx_opt_async_pre_txn_delay = c_fn('obx_opt_async_pre_txn_delay', None, [OBX_store_options_p, ctypes.c_uint32])

# OBX_C_API void obx_opt_async_pre_txn_delay4(OBX_store_options* opt, uint32_t delay_micros, uint32_t delay2_micros, size_t min_queue_length_for_delay2);
obx_opt_async_pre_txn_delay4 = c_fn('obx_opt_async_pre_txn_delay4', None,
                                    [OBX_store_options_p, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_size_t])

# OBX_C_API void obx_opt_async_post_txn_delay(OBX_store_options* opt, uint32_t delay_micros);
obx_opt_async_post_txn_delay = c_fn('obx_opt_async_post_txn_delay', None, [OBX_store_options_p, ctypes.c_uint32])

# OBX_C_API void obx_opt_async_post_txn_delay5(OBX_store_options* opt, uint32_t delay_micros, uint32_t delay2_micros, size_t min_queue_length_for_delay2, bool subtract_processing_time);
obx_opt_async_post_txn_delay5 = c_fn('obx_opt_async_post_txn_delay5', None,
                                     [OBX_store_options_p, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_size_t,
                                      ctypes.c_bool])

# OBX_C_API void obx_opt_async_minor_refill_threshold(OBX_store_options* opt, size_t queue_length);
obx_opt_async_minor_refill_threshold = c_fn('obx_opt_async_minor_refill_threshold', None,
                                            [OBX_store_options_p, ctypes.c_size_t])

# OBX_C_API void obx_opt_async_minor_refill_max_count(OBX_store_options* opt, uint32_t value);
obx_opt_async_minor_refill_max_count = c_fn('obx_opt_async_minor_refill_max_count', None,
                                            [OBX_store_options_p, ctypes.c_uint32])

# OBX_C_API void obx_opt_async_max_tx_pool_size(OBX_store_options* opt, size_t value);
obx_opt_async_max_tx_pool_size = c_fn('obx_opt_async_max_tx_pool_size', None, [OBX_store_options_p, ctypes.c_size_t])

# OBX_C_API void obx_opt_async_object_bytes_max_cache_size(OBX_store_options* opt, uint64_t value);
obx_opt_async_object_bytes_max_cache_size = c_fn('obx_opt_async_object_bytes_max_cache_size', None,
                                                 [OBX_store_options_p, ctypes.c_uint64])

# OBX_C_API void obx_opt_async_object_bytes_max_size_to_cache(OBX_store_options* opt, uint64_t value);
obx_opt_async_object_bytes_max_size_to_cache = c_fn('obx_opt_async_object_bytes_max_size_to_cache', None,
                                                    [OBX_store_options_p, ctypes.c_uint64])

#typedef void obx_log_callback(OBXLogLevel log_level, const char* message, size_t message_size, void* user_data);
obx_log_callback_fn = ctypes.CFUNCTYPE(None, OBXLogLevel, ctypes.c_char_p, ctypes.c_size_t, ctypes.c_voidp)

# OBX_C_API void obx_opt_log_callback(OBX_store_options* opt, obx_log_callback* callback, void* user_data);
obx_opt_log_callback = c_fn('obx_opt_log_callback', None, [OBX_store_options_p, obx_log_callback_fn, ctypes.c_voidp])

# OBX_C_API void obx_opt_backup_restore(OBX_store_options* opt, const char* backup_file, uint32_t flags);
obx_opt_backup_restore = c_fn('obx_opt_backup_restore', None,
                              [OBX_store_options_p, ctypes.c_char_p, OBXBackupRestoreFlags])

# OBX_C_API const char* obx_opt_get_directory(OBX_store_options* opt);
obx_opt_get_directory = c_fn('obx_opt_get_directory', ctypes.c_char_p, [OBX_store_options_p])

# OBX_C_API uint64_t obx_opt_get_max_db_size_in_kb(OBX_store_options* opt);
obx_opt_get_max_db_size_in_kb = c_fn('obx_opt_get_max_db_size_in_kb', ctypes.c_uint64, [OBX_store_options_p])

# OBX_C_API uint64_t obx_opt_get_max_data_size_in_kb(OBX_store_options* opt);
obx_opt_get_max_data_size_in_kb = c_fn('obx_opt_get_max_data_size_in_kb', ctypes.c_uint64, [OBX_store_options_p])

# OBX_C_API uint32_t obx_opt_get_debug_flags(OBX_store_options* opt);
obx_opt_get_debug_flags = c_fn('obx_opt_get_debug_flags', ctypes.c_uint32, [OBX_store_options_p])

# OBX_C_API void obx_opt_free(OBX_store_options* opt);
obx_opt_free = c_fn('obx_opt_free', None, [])

# OBX_store* (const OBX_store_options* options);
obx_store_open = c_fn('obx_store_open', OBX_store_p, [OBX_store_options_p])

# obx_err (OBX_store* store);
obx_store_close = c_fn_rc('obx_store_close', [OBX_store_p])

# obx_err obx_remove_db_files(const const* directory);
obx_remove_db_files = c_fn_rc('obx_remove_db_files', [ctypes.c_char_p])  # TODO provide a python wrapper

# OBX_txn* (OBX_store* store);
obx_txn_write = c_fn('obx_txn_write', OBX_txn_p, [OBX_store_p])

# OBX_txn* (OBX_store* store);
obx_txn_read = c_fn('obx_txn_read', OBX_txn_p, [OBX_store_p])

# obx_err (OBX_txn* txn)
obx_txn_close = c_fn_rc('obx_txn_close', [OBX_txn_p])

# obx_err (OBX_txn* txn);
obx_txn_abort = c_fn_rc('obx_txn_abort', [OBX_txn_p])

# obx_err (OBX_txn* txn);
obx_txn_success = c_fn_rc('obx_txn_success', [OBX_txn_p])

# OBX_box* (OBX_store* store, obx_schema_id entity_id);
obx_box = c_fn('obx_box', OBX_box_p, [OBX_store_p, obx_schema_id])

# obx_err (OBX_box* box, obx_id id, const void** data, size_t* size);
obx_box_get = c_fn_nocheck('obx_box_get', obx_err, [
    OBX_box_p, obx_id, ctypes.POINTER(ctypes.c_void_p), ctypes.POINTER(ctypes.c_size_t)])

# OBX_bytes_array* (OBX_box* box);
obx_box_get_all = c_fn('obx_box_get_all', OBX_bytes_array_p, [OBX_box_p])

# obx_id (OBX_box* box, obx_id id_or_zero);
obx_box_id_for_put = c_fn('obx_box_id_for_put', obx_id, [OBX_box_p, obx_id])

# obx_err (OBX_box* box, uint64_t count, obx_id* out_first_id);
obx_box_ids_for_put = c_fn_rc('obx_box_ids_for_put', [
    OBX_box_p, ctypes.c_uint64, ctypes.POINTER(obx_id)])

# obx_err (OBX_box* box, obx_id id, const void* data, size_t size);
obx_box_put = c_fn_rc('obx_box_put', [OBX_box_p, obx_id, ctypes.c_void_p, ctypes.c_size_t])

# obx_err (OBX_box* box, const OBX_bytes_array* objects, const obx_id* ids, OBXPutMode mode);
obx_box_put_many = c_fn_rc('obx_box_put_many', [
    OBX_box_p, OBX_bytes_array_p, ctypes.POINTER(obx_id), OBXPutMode])

# obx_err (OBX_box* box, obx_id id);
obx_box_remove = c_fn_nocheck('obx_box_remove', obx_err, [OBX_box_p, obx_id])

# obx_err (OBX_box* box, uint64_t* out_count);
obx_box_remove_all = c_fn_rc('obx_box_remove_all', [
    OBX_box_p, ctypes.POINTER(ctypes.c_uint64)])

# obx_err (OBX_box* box, bool* out_is_empty);
obx_box_is_empty = c_fn_rc('obx_box_is_empty', [
    OBX_box_p, ctypes.POINTER(ctypes.c_bool)])

# obx_err obx_box_count(OBX_box* box, uint64_t limit, uint64_t* out_count);
obx_box_count = c_fn_rc('obx_box_count', [
    OBX_box_p, ctypes.c_uint64, ctypes.POINTER(ctypes.c_uint64)])

# OBX_query_builder* obx_query_builder(OBX_store* store, obx_schema_id entity_id);
obx_query_builder = c_fn('obx_query_builder', OBX_query_builder_p, [OBX_store_p, obx_schema_id])

# OBX_C_API obx_err obx_qb_close(OBX_query_builder* builder);
obx_qb_close = c_fn_rc('obx_qb_close', [OBX_query_builder_p])

# OBX_C_API OBX_query* obx_query(OBX_query_builder* builder);
obx_query = c_fn('obx_query', OBX_query_p, [OBX_query_builder_p])

# OBX_C_API obx_err obx_qb_error_code(OBX_query_builder* builder);
obx_qb_error_code = c_fn_rc('obx_qb_error_code', [OBX_query_builder_p])

# OBX_C_API const char* obx_qb_error_message(OBX_query_builder* builder);
obx_qb_error_message = c_fn('obx_qb_error_message', ctypes.c_char_p, [OBX_query_builder_p])

# OBX_C_API obx_qb_cond obx_qb_null(OBX_query_builder* builder, obx_schema_id property_id);
obx_qb_null = c_fn('obx_qb_null', obx_qb_cond, [OBX_query_builder_p, obx_schema_id])

# OBX_C_API obx_qb_cond obx_qb_not_null(OBX_query_builder* builder, obx_schema_id property_id);
obx_qb_not_null = c_fn('obx_qb_not_null', obx_qb_cond, [OBX_query_builder_p, obx_schema_id])

# OBX_C_API obx_qb_cond obx_qb_equals_string(OBX_query_builder* builder, obx_schema_id property_id, const char* value,
#                                            bool case_sensitive);
obx_qb_equals_string = c_fn('obx_qb_equals_string', obx_qb_cond,
                            [OBX_query_builder_p, obx_schema_id, ctypes.c_char_p, ctypes.c_bool])

# OBX_C_API obx_qb_co nd obx_qb_not_equals_string(OBX_query_builder* builder, obx_schema_id property_id, const char* value,
#                                               bool case_sensitive);
obx_qb_not_equals_string = c_fn('obx_qb_not_equals_string', obx_qb_cond,
                                [OBX_query_builder_p, obx_schema_id, ctypes.c_char_p, ctypes.c_bool])

# OBX_C_API obx_qb_cond obx_qb_contains_string(OBX_query_builder* builder, obx_schema_id property_id, const char* value,
#                                              bool case_sensitive);
obx_qb_contains_string = c_fn('obx_qb_contains_string', obx_qb_cond,
                              [OBX_query_builder_p, obx_schema_id, ctypes.c_char_p, ctypes.c_bool])

# OBX_C_API obx_qb_cond obx_qb_contains_element_string(OBX_query_builder* builder, obx_schema_id property_id,
#                                                      const char* value, bool case_sensitive);
obx_qb_contains_element_string = c_fn('obx_qb_contains_element_string', obx_qb_cond,
                                      [OBX_query_builder_p, obx_schema_id, ctypes.c_char_p, ctypes.c_bool])

# OBX_C_API obx_qb_cond obx_qb_contains_key_value_string(OBX_query_builder* builder, obx_schema_id property_id,
#                                                        const char* key, const char* value, bool case_sensitive);
obx_qb_contains_key_value_string = c_fn('obx_qb_contains_key_value_string', obx_qb_cond,
                                        [OBX_query_builder_p, obx_schema_id, ctypes.c_char_p, ctypes.c_char_p,
                                         ctypes.c_bool])

# OBX_C_API obx_qb_cond obx_qb_starts_with_string(OBX_query_builder* builder, obx_schema_id property_id,
#                                                 const char* value, bool case_sensitive);
obx_qb_starts_with_string = c_fn('obx_qb_starts_with_string', obx_qb_cond,
                                 [OBX_query_builder_p, obx_schema_id, ctypes.c_char_p, ctypes.c_bool])

# OBX_C_API obx_qb_cond obx_qb_ends_with_string(OBX_query_builder* builder, obx_schema_id property_id, const char* value,
#                                               bool case_sensitive);
obx_qb_ends_with_string = c_fn('obx_qb_ends_with_string', obx_qb_cond,
                               [OBX_query_builder_p, obx_schema_id, ctypes.c_char_p, ctypes.c_bool])

# OBX_C_API obx_qb_cond obx_qb_greater_than_string(OBX_query_builder* builder, obx_schema_id property_id,
#                                                  const char* value, bool case_sensitive);
obx_qb_greater_than_string = c_fn('obx_qb_greater_than_string', obx_qb_cond,
                                  [OBX_query_builder_p, obx_schema_id, ctypes.c_char_p, ctypes.c_bool])

# OBX_C_API obx_qb_cond obx_qb_greater_or_equal_string(OBX_query_builder* builder, obx_schema_id property_id,
#                                                      const char* value, bool case_sensitive);
obx_qb_greater_or_equal_string = c_fn('obx_qb_greater_or_equal_string', obx_qb_cond,
                                      [OBX_query_builder_p, obx_schema_id, ctypes.c_char_p, ctypes.c_bool])

# OBX_C_API obx_qb_cond obx_qb_less_than_string(OBX_query_builder* builder, obx_schema_id property_id, const char* value,
#                                               bool case_sensitive);
obx_qb_less_than_string = c_fn('obx_qb_less_than_string', obx_qb_cond,
                               [OBX_query_builder_p, obx_schema_id, ctypes.c_char_p, ctypes.c_bool])

# OBX_C_API obx_qb_cond obx_qb_less_or_equal_string(OBX_query_builder* builder, obx_schema_id property_id,
#                                                   const char* value, bool case_sensitive);
obx_qb_less_or_equal_string = c_fn('obx_qb_less_or_equal_string', obx_qb_cond,
                                   [OBX_query_builder_p, obx_schema_id, ctypes.c_char_p, ctypes.c_bool])

# OBX_C_API obx_qb_cond obx_qb_in_strings(OBX_query_builder* builder, obx_schema_id property_id,
#                                         const char* const values[], size_t count, bool case_sensitive);
obx_qb_in_strings = c_fn('obx_qb_in_strings', obx_qb_cond,
                         [OBX_query_builder_p, obx_schema_id, ctypes.POINTER(ctypes.c_char_p), ctypes.c_size_t,
                          ctypes.c_bool])

# OBX_C_API obx_qb_cond obx_qb_any_equals_string(OBX_query_builder* builder, obx_schema_id property_id, const char* value,
#                                                bool case_sensitive);
obx_qb_any_equals_string = c_fn('obx_qb_any_equals_string', obx_qb_cond,
                                [OBX_query_builder_p, obx_schema_id, ctypes.c_char_p, ctypes.c_bool])

# OBX_C_API obx_qb_cond obx_qb_equals_int(OBX_query_builder* builder, obx_schema_id property_id, int64_t value);
obx_qb_equals_int = c_fn('obx_qb_equals_int', obx_qb_cond, [OBX_query_builder_p, obx_schema_id, ctypes.c_int64])

# OBX_C_API obx_qb_cond obx_qb_not_equals_int(OBX_query_builder* builder, obx_schema_id property_id, int64_t value);
obx_qb_not_equals_int = c_fn('obx_qb_not_equals_int', obx_qb_cond, [OBX_query_builder_p, obx_schema_id, ctypes.c_int64])

# OBX_C_API obx_qb_cond obx_qb_greater_than_int(OBX_query_builder* builder, obx_schema_id property_id, int64_t value);
obx_qb_greater_than_int = c_fn('obx_qb_greater_than_int', obx_qb_cond,
                               [OBX_query_builder_p, obx_schema_id, ctypes.c_int64])

# OBX_C_API obx_qb_cond obx_qb_greater_or_equal_int(OBX_query_builder* builder, obx_schema_id property_id, int64_t value);
obx_qb_greater_or_equal_int = c_fn('obx_qb_greater_or_equal_int', obx_qb_cond,
                                   [OBX_query_builder_p, obx_schema_id, ctypes.c_int64])

# OBX_C_API obx_qb_cond obx_qb_less_than_int(OBX_query_builder* builder, obx_schema_id property_id, int64_t value);
obx_qb_less_than_int = c_fn('obx_qb_less_than_int', obx_qb_cond, [OBX_query_builder_p, obx_schema_id, ctypes.c_int64])

# OBX_C_API obx_qb_cond obx_qb_less_or_equal_int(OBX_query_builder* builder, obx_schema_id property_id, int64_t value);
obx_qb_less_or_equal_int = c_fn('obx_qb_less_or_equal_int', obx_qb_cond,
                                [OBX_query_builder_p, obx_schema_id, ctypes.c_int64])

# OBX_C_API obx_qb_cond obx_qb_between_2ints(OBX_query_builder* builder, obx_schema_id property_id, int64_t value_a,
#                                            int64_t value_b);
obx_qb_between_2ints = c_fn('obx_qb_between_2ints', obx_qb_cond,
                            [OBX_query_builder_p, obx_schema_id, ctypes.c_int64, ctypes.c_int64])

# OBX_C_API obx_qb_cond obx_qb_in_int64s(OBX_query_builder* builder, obx_schema_id property_id, const int64_t values[],
#                                        size_t count);
obx_qb_in_int64s = c_fn('obx_qb_in_int64s', obx_qb_cond,
                        [OBX_query_builder_p, obx_schema_id, ctypes.POINTER(ctypes.c_int64), ctypes.c_size_t])

# OBX_C_API obx_qb_cond obx_qb_not_in_int64s(OBX_query_builder* builder, obx_schema_id property_id,
#                                            const int64_t values[], size_t count);
obx_qb_not_in_int64s = c_fn('obx_qb_not_in_int64s', obx_qb_cond,
                            [OBX_query_builder_p, obx_schema_id, ctypes.POINTER(ctypes.c_int64), ctypes.c_size_t])

# OBX_C_API obx_qb_cond obx_qb_in_int32s(OBX_query_builder* builder, obx_schema_id property_id, const int32_t values[],
#                                        size_t count);
obx_qb_in_int32s = c_fn('obx_qb_in_int32s', obx_qb_cond,
                        [OBX_query_builder_p, obx_schema_id, ctypes.POINTER(ctypes.c_int32), ctypes.c_size_t])

# OBX_C_API obx_qb_cond obx_qb_not_in_int32s(OBX_query_builder* builder, obx_schema_id property_id,
#                                            const int32_t values[], size_t count);
obx_qb_not_in_int32s = c_fn('obx_qb_not_in_int32s', obx_qb_cond,
                            [OBX_query_builder_p, obx_schema_id, ctypes.POINTER(ctypes.c_int32), ctypes.c_size_t])

# OBX_C_API obx_qb_cond obx_qb_greater_than_double(OBX_query_builder* builder, obx_schema_id property_id, double value);
obx_qb_greater_than_double = c_fn('obx_qb_greater_than_double', obx_qb_cond,
                                  [OBX_query_builder_p, obx_schema_id, ctypes.c_double])

# OBX_C_API obx_qb_cond obx_qb_greater_or_equal_double(OBX_query_builder* builder, obx_schema_id property_id,
#                                                      double value);
obx_qb_greater_or_equal_double = c_fn('obx_qb_greater_or_equal_double', obx_qb_cond,
                                      [OBX_query_builder_p, obx_schema_id, ctypes.c_double])

# OBX_C_API obx_qb_cond obx_qb_less_than_double(OBX_query_builder* builder, obx_schema_id property_id, double value);
obx_qb_less_than_double = c_fn('obx_qb_less_than_double', obx_qb_cond,
                               [OBX_query_builder_p, obx_schema_id, ctypes.c_double])

# OBX_C_API obx_qb_cond obx_qb_less_or_equal_double(OBX_query_builder* builder, obx_schema_id property_id, double value);
obx_qb_less_or_equal_double = c_fn('obx_qb_less_or_equal_double', obx_qb_cond,
                                   [OBX_query_builder_p, obx_schema_id, ctypes.c_double])

# OBX_C_API obx_qb_cond obx_qb_between_2doubles(OBX_query_builder* builder, obx_schema_id property_id, double value_a,
#                                               double value_b);
obx_qb_between_2doubles = c_fn('obx_qb_between_2doubles', obx_qb_cond,
                               [OBX_query_builder_p, obx_schema_id, ctypes.c_double, ctypes.c_double])

# OBX_C_API obx_qb_cond obx_qb_equals_bytes(OBX_query_builder* builder, obx_schema_id property_id, const void* value,
#                                           size_t size);
obx_qb_equals_bytes = c_fn('obx_qb_equals_bytes', obx_qb_cond,
                           [OBX_query_builder_p, obx_schema_id, ctypes.c_void_p, ctypes.c_size_t])

# OBX_C_API obx_qb_cond obx_qb_greater_than_bytes(OBX_query_builder* builder, obx_schema_id property_id,
#                                                 const void* value, size_t size);
obx_qb_greater_than_bytes = c_fn('obx_qb_greater_than_bytes', obx_qb_cond,
                                 [OBX_query_builder_p, obx_schema_id, ctypes.c_void_p, ctypes.c_size_t])

# OBX_C_API obx_qb_cond obx_qb_greater_or_equal_bytes(OBX_query_builder* builder, obx_schema_id property_id,
#                                                     const void* value, size_t size);
obx_qb_greater_or_equal_bytes = c_fn('obx_qb_greater_or_equal_bytes', obx_qb_cond,
                                     [OBX_query_builder_p, obx_schema_id, ctypes.c_void_p, ctypes.c_size_t])

# OBX_C_API obx_qb_cond obx_qb_less_than_bytes(OBX_query_builder* builder, obx_schema_id property_id, const void* value,
#                                              size_t size);
obx_qb_less_than_bytes = c_fn('obx_qb_less_than_bytes', obx_qb_cond,
                              [OBX_query_builder_p, obx_schema_id, ctypes.c_void_p, ctypes.c_size_t])

# OBX_C_API obx_qb_cond obx_qb_less_or_equal_bytes(OBX_query_builder* builder, obx_schema_id property_id,
#                                                  const void* value, size_t size);
obx_qb_less_or_equal_bytes = c_fn('obx_qb_less_or_equal_bytes', obx_qb_cond,
                                  [OBX_query_builder_p, obx_schema_id, ctypes.c_void_p, ctypes.c_size_t])

# OBX_C_API obx_qb_cond obx_qb_all(OBX_query_builder* builder, const obx_qb_cond conditions[], size_t count);
obx_qb_all = c_fn('obx_qb_all', obx_qb_cond, [OBX_query_builder_p, obx_qb_cond_p, ctypes.c_size_t])

# OBX_C_API obx_qb_cond obx_qb_any(OBX_query_builder* builder, const obx_qb_cond conditions[], size_t count);
obx_qb_any = c_fn('obx_qb_any', obx_qb_cond, [OBX_query_builder_p, obx_qb_cond_p, ctypes.c_size_t])

# OBX_C_API obx_err obx_qb_param_alias(OBX_query_builder* builder, const char* alias);
obx_qb_param_alias = c_fn_rc('obx_qb_param_alias', [OBX_query_builder_p, ctypes.c_char_p])

# OBX_C_API obx_err obx_query_param_string(OBX_query* query, obx_schema_id entity_id, obx_schema_id property_id, const char* value);
obx_query_param_string = c_fn_rc('obx_query_param_string', [OBX_query_p, obx_schema_id, obx_schema_id, ctypes.c_char_p])

# OBX_C_API obx_err obx_query_param_int(OBX_query* query, obx_schema_id entity_id, obx_schema_id property_id, int64_t value);
obx_query_param_int = c_fn_rc('obx_query_param_int', [OBX_query_p, obx_schema_id, obx_schema_id, ctypes.c_int64])

# OBX_C_API obx_err obx_query_param_vector_float32(OBX_query* query, obx_schema_id entity_id, obx_schema_id property_id, const float* value, size_t element_count);
obx_query_param_vector_float32 = c_fn_rc('obx_query_param_vector_float32',
                                         [OBX_query_p, obx_schema_id, obx_schema_id, ctypes.POINTER(ctypes.c_float),
                                          ctypes.c_size_t])

# OBX_C_API obx_err obx_query_param_alias_vector_float32(OBX_query* query, const char* alias, const float* value, size_t element_count);
obx_query_param_alias_vector_float32 = c_fn_rc('obx_query_param_alias_vector_float32',
                                               [OBX_query_p, ctypes.c_char_p, ctypes.POINTER(ctypes.c_float),
                                                ctypes.c_size_t])

# OBX_C_API obx_err obx_query_param_alias_string(OBX_query* query, const char* alias, const char* value);
obx_query_param_alias_string = c_fn_rc('obx_query_param_alias_string', [OBX_query_p, ctypes.c_char_p, ctypes.c_char_p])

# OBX_C_API obx_err obx_query_param_alias_int(OBX_query* query, const char* alias, int64_t value);
obx_query_param_alias_int = c_fn_rc('obx_query_param_alias_int', [OBX_query_p, ctypes.c_char_p, ctypes.c_int64])

# OBX_C_API obx_err obx_qb_order(OBX_query_builder* builder, obx_schema_id property_id, OBXOrderFlags flags);
obx_qb_order = c_fn_rc('obx_qb_order', [OBX_query_builder_p, obx_schema_id, OBXOrderFlags])

# OBX_C_API obx_qb_cond obx_qb_nearest_neighbors_f32(OBX_query_builder* builder, obx_schema_id vector_property_id, const float* query_vector, size_t max_result_count)
obx_qb_nearest_neighbors_f32 = c_fn_qb_cond('obx_qb_nearest_neighbors_f32',
                                            [OBX_query_builder_p, obx_schema_id, ctypes.POINTER(ctypes.c_float),
                                             ctypes.c_size_t])

# OBX_C_API OBX_query* obx_query(OBX_query_builder* builder);
obx_query = c_fn('obx_query', OBX_query_p, [OBX_query_builder_p])

# OBX_C_API obx_err obx_query_close(OBX_query* query);
obx_query_close = c_fn_rc('obx_query_close', [OBX_query_p])

# OBX_C_API OBX_query* obx_query_clone(OBX_query* query);
obx_query_clone = c_fn('obx_query_clone', OBX_query_p, [OBX_query_p])

# OBX_C_API obx_err obx_query_offset(OBX_query* query, size_t offset);
obx_query_offset = c_fn_rc('obx_query_offset', [OBX_query_p, ctypes.c_size_t])

# OBX_C_API obx_err obx_query_offset_limit(OBX_query* query, size_t offset, size_t limit);
obx_query_offset_limit = c_fn_rc('obx_query_offset_limit', [OBX_query_p, ctypes.c_size_t, ctypes.c_size_t])

# OBX_C_API obx_err obx_query_limit(OBX_query* query, size_t limit);
obx_query_limit = c_fn_rc('obx_query_limit', [OBX_query_p, ctypes.c_size_t])

# OBX_C_API OBX_bytes_array* obx_query_find(OBX_query* query);
obx_query_find = c_fn('obx_query_find', OBX_bytes_array_p, [OBX_query_p])

# OBX_C_API obx_err obx_query_find_first(OBX_query* query, const void** data, size_t* size);
obx_query_find_first = c_fn_rc('obx_query_find_first',
                               [OBX_query_p, ctypes.POINTER(ctypes.c_void_p), ctypes.POINTER(ctypes.c_size_t)])

# OBX_C_API obx_err obx_query_find_unique(OBX_query* query, const void** data, size_t* size);
obx_query_find_unique = c_fn_rc('obx_query_find_unique',
                                [OBX_query_p, ctypes.POINTER(ctypes.c_void_p), ctypes.POINTER(ctypes.c_size_t)])

# OBX_C_API OBX_bytes_score_array* obx_query_find_with_scores(OBX_query* query);
obx_query_find_with_scores = c_fn('obx_query_find_with_scores', OBX_bytes_score_array_p, [OBX_query_p])

# typedef bool obx_data_visitor(void* user_data, const void* data, size_t size);

# OBX_C_API obx_err obx_query_visit(OBX_query* query, obx_data_visitor* visitor, void* user_data);
# obx_query_visit = fn('obx_query_visit', obx_err, [OBX_query_p, obx_data_visitor_p, ctypes.c_void_p])

# OBX_C_API OBX_id_array* obx_query_find_ids(OBX_query* query);
obx_query_find_ids = c_fn('obx_query_find_ids', OBX_id_array_p, [OBX_query_p])

# OBX_C_API OBX_id_score_array* obx_query_find_ids_with_scores(OBX_query* query);
obx_query_find_ids_with_scores = c_fn('obx_query_find_ids_with_scores', OBX_id_score_array_p, [OBX_query_p])

# OBX_C_API OBX_id_array* obx_query_find_ids_by_score(OBX_query* query);
obx_query_find_ids_by_score = c_fn('obx_query_find_ids_by_score', OBX_id_array_p, [OBX_query_p])

# OBX_C_API obx_err obx_query_count(OBX_query* query, uint64_t* out_count);
obx_query_count = c_fn_rc('obx_query_count', [OBX_query_p, ctypes.POINTER(ctypes.c_uint64)])

# OBX_C_API obx_err obx_query_remove(OBX_query* query, uint64_t* out_count);
obx_query_remove = c_fn_rc('obx_query_remove', [OBX_query_p, ctypes.POINTER(ctypes.c_uint64)])

# OBX_C_API const char* obx_query_describe(OBX_query* query);
obx_query_describe = c_fn('obx_query_describe', ctypes.c_char_p, [OBX_query_p])

# OBX_C_API const char* obx_query_describe_params(OBX_query* query);
obx_query_describe_params = c_fn('obx_query_describe_params', ctypes.c_char_p, [OBX_query_p])

# OBX_bytes_array* (size_t count);
obx_bytes_array = c_fn('obx_bytes_array', OBX_bytes_array_p, [ctypes.c_size_t])

# obx_err (OBX_bytes_array* array, size_t index, const void* data, size_t size);
obx_bytes_array_set = c_fn_rc('obx_bytes_array_set', [
    OBX_bytes_array_p, ctypes.c_size_t, ctypes.c_void_p, ctypes.c_size_t])

# void (OBX_bytes_array * array);
obx_bytes_array_free = c_fn('obx_bytes_array_free', None, [OBX_bytes_array_p])

# OBX_C_API void obx_id_array_free(OBX_id_array* array);
obx_id_array_free = c_fn('obx_id_array_free', None, [OBX_id_array_p])

# OBX_C_API void obx_bytes_score_array_free(OBX_bytes_score_array* array)
obx_bytes_score_array_free = c_fn('obx_bytes_score_array_free', None, [OBX_bytes_score_array_p])

# OBX_C_API void obx_id_score_array_free(OBX_id_score_array* array)
obx_id_score_array_free = c_fn('obx_id_score_array_free', None, [OBX_id_score_array_p])

OBXPropertyType_Bool = 1
OBXPropertyType_Byte = 2
OBXPropertyType_Short = 3
OBXPropertyType_Char = 4
OBXPropertyType_Int = 5
OBXPropertyType_Long = 6
OBXPropertyType_Float = 7
OBXPropertyType_Double = 8
OBXPropertyType_String = 9
OBXPropertyType_Date = 10
OBXPropertyType_Relation = 11
OBXPropertyType_DateNano = 12
OBXPropertyType_Flex = 13
OBXPropertyType_BoolVector = 22
OBXPropertyType_ByteVector = 23
OBXPropertyType_ShortVector = 24
OBXPropertyType_CharVector = 25
OBXPropertyType_IntVector = 26
OBXPropertyType_LongVector = 27
OBXPropertyType_FloatVector = 28
OBXPropertyType_DoubleVector = 29
OBXPropertyType_StringVector = 30

OBXPropertyFlags_ID = 1
OBXPropertyFlags_NON_PRIMITIVE_TYPE = 2
OBXPropertyFlags_NOT_NULL = 4
OBXPropertyFlags_INDEXED = 8
OBXPropertyFlags_RESERVED = 16
OBXPropertyFlags_UNIQUE = 32
OBXPropertyFlags_ID_MONOTONIC_SEQUENCE = 64
OBXPropertyFlags_ID_SELF_ASSIGNABLE = 128
OBXPropertyFlags_INDEX_PARTIAL_SKIP_NULL = 256
OBXPropertyFlags_INDEX_PARTIAL_SKIP_ZERO = 512
OBXPropertyFlags_VIRTUAL = 1024
OBXPropertyFlags_INDEX_HASH = 2048
OBXPropertyFlags_INDEX_HASH64 = 4096
OBXPropertyFlags_UNSIGNED = 8192

OBXDebugFlags_LOG_TRANSACTIONS_READ = 1
OBXDebugFlags_LOG_TRANSACTIONS_WRITE = 2
OBXDebugFlags_LOG_QUERIES = 4
OBXDebugFlags_LOG_QUERY_PARAMETERS = 8
OBXDebugFlags_LOG_ASYNC_QUEUE = 16
OBXDebugFlags_LOG_CACHE_HITS = 32
OBXDebugFlags_LOG_CACHE_ALL = 64
OBXDebugFlags_LOG_TREE = 128
OBXDebugFlags_LOG_EXCEPTION_STACK_TRACE = 256
OBXDebugFlags_RUN_THREADING_SELF_TEST = 512

# Standard put ("insert or update")
OBXPutMode_PUT = 1

# Put succeeds only if the entity does not exist yet.
OBXPutMode_INSERT = 2

# Put succeeds only if the entity already exist.
OBXPutMode_UPDATE = 3

# The given ID (non-zero) is guaranteed to be new; don't use unless you know exactly what you are doing!
# This is primarily used internally. Wrong usage leads to inconsistent data (e.g. index data not updated)!
OBXPutMode_PUT_ID_GUARANTEED_TO_BE_NEW = 4

# Reverts the order from ascending (default) to descending.
OBXOrderFlags_DESCENDING = 1

# Makes upper case letters (e.g. "Z") be sorted before lower case letters (e.g. "a").
# If not specified, the default is case insensitive for ASCII characters.
OBXOrderFlags_CASE_SENSITIVE = 2

# For scalars only: changes the comparison to unsigned (default is signed).
OBXOrderFlags_UNSIGNED = 4

# null values will be put last.
# If not specified, by default null values will be put first.
OBXOrderFlags_NULLS_LAST = 8

# null values should be treated equal to zero (scalars only).
OBXOrderFlags_NULLS_ZERO = 16

OBXHnswFlags_NONE = 0
OBXHnswFlags_DEBUG_LOGS = 1
OBXHnswFlags_DEBUG_LOGS_DETAILED = 2
OBXHnswFlags_VECTOR_CACHE_SIMD_PADDING_OFF = 4
OBXHnswFlags_REPARATION_LIMIT_CANDIDATES = 8

OBXVectorDistanceType_UNKNOWN = 0
OBXVectorDistanceType_EUCLIDEAN = 1
OBXVectorDistanceType_COSINE = 2
OBXVectorDistanceType_DOT_PRODUCT = 3
OBXVectorDistanceType_DOT_PRODUCT_NON_NORMALIZED = 10

OBXPutPaddingMode_PaddingAutomatic = 1
OBXPutPaddingMode_PaddingAllowedByBuffer = 2
OBXPutPaddingMode_PaddingByCaller = 3

OBXValidateOnOpenPagesFlags_None = 0
OBXValidateOnOpenPagesFlags_VisitLeafPages = 1

OBXValidateOnOpenKvFlags_None = 0

OBXBackupRestoreFlags_None = 0
OBXBackupRestoreFlags_OverwriteExistingData = 1


# Sync API

class OBX_sync(ctypes.Structure):
    pass


OBX_sync_p = ctypes.POINTER(OBX_sync)


class OBX_sync_server(ctypes.Structure):
    pass


OBX_sync_server_p = ctypes.POINTER(OBX_sync_server)

OBXSyncCredentialsType = ctypes.c_int
OBXRequestUpdatesMode = ctypes.c_int
OBXSyncState = ctypes.c_int
OBXSyncCode = ctypes.c_int


class SyncCredentialsType(IntEnum):
    NONE = 1
    SHARED_SECRET = 2  # Deprecated, use SHARED_SECRET_SIPPED instead
    GOOGLE_AUTH = 3
    SHARED_SECRET_SIPPED = 4  # Uses shared secret to create a hashed credential
    OBX_ADMIN_USER = 5  # ObjectBox admin users (username/password)
    USER_PASSWORD = 6  # Generic credential type for admin users
    JWT_ID = 7  # JSON Web Token (JWT): ID token with user identity
    JWT_ACCESS = 8  # JSON Web Token (JWT): access token for resources
    JWT_REFRESH = 9  # JSON Web Token (JWT): refresh token
    JWT_CUSTOM = 10  # JSON Web Token (JWT): custom token type


class RequestUpdatesMode(IntEnum):
    MANUAL = 0  # No updates by default, must call obx_sync_updates_request() manually
    AUTO = 1  # Same as calling obx_sync_updates_request(sync, TRUE)
    AUTO_NO_PUSHES = 2  # Same as calling obx_sync_updates_request(sync, FALSE)


class SyncState(IntEnum):
    CREATED = 1
    STARTED = 2
    CONNECTED = 3
    LOGGED_IN = 4
    DISCONNECTED = 5
    STOPPED = 6
    DEAD = 7


class OBXSyncError(IntEnum):
    REJECT_TX_NO_PERMISSION = 1  # Sync client received rejection of transaction writes due to missing permissions


class OBXSyncObjectType(IntEnum):
    FlatBuffers = 1
    String = 2
    Raw = 3


class OBX_sync_change(ctypes.Structure):
    _fields_ = [
        ('entity_id', obx_schema_id),
        ('puts', ctypes.POINTER(OBX_id_array)),
        ('removals', ctypes.POINTER(OBX_id_array)),
    ]


class OBX_sync_change_array(ctypes.Structure):
    _fields_ = [
        ('list', ctypes.POINTER(OBX_sync_change)),
        ('count', ctypes.c_size_t),
    ]


class OBX_sync_object(ctypes.Structure):
    _fields_ = [
        ('type', ctypes.c_int),  # OBXSyncObjectType
        ('id', ctypes.c_uint64),
        ('data', ctypes.c_void_p),
        ('size', ctypes.c_size_t),
    ]


class OBX_sync_msg_objects(ctypes.Structure):
    _fields_ = [
        ('topic', ctypes.c_void_p),
        ('topic_size', ctypes.c_size_t),
        ('objects', ctypes.POINTER(OBX_sync_object)),
        ('count', ctypes.c_size_t),
    ]


class OBX_sync_msg_objects_builder(ctypes.Structure):
    pass


OBX_sync_msg_objects_builder_p = ctypes.POINTER(OBX_sync_msg_objects_builder)

# Define callback types for sync listeners
OBX_sync_listener_connect = ctypes.CFUNCTYPE(None, ctypes.c_void_p)
OBX_sync_listener_disconnect = ctypes.CFUNCTYPE(None, ctypes.c_void_p)
OBX_sync_listener_login = ctypes.CFUNCTYPE(None, ctypes.c_void_p)
OBX_sync_listener_login_failure = ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_int)  # arg, OBXSyncCode
OBX_sync_listener_complete = ctypes.CFUNCTYPE(None, ctypes.c_void_p)
OBX_sync_listener_error = ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_int)  # arg, OBXSyncError
OBX_sync_listener_change = ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.POINTER(OBX_sync_change_array))
OBX_sync_listener_server_time = ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_int64)
OBX_sync_listener_msg_objects = ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.POINTER(OBX_sync_msg_objects))

# OBX_sync* obx_sync(OBX_store* store, const char* server_url);
obx_sync = c_fn("obx_sync", OBX_sync_p, [OBX_store_p, ctypes.c_char_p])

# OBX_sync* obx_sync_urls(OBX_store* store, const char* server_urls[], size_t server_urls_count);
obx_sync_urls = c_fn("obx_sync_urls", OBX_sync_p, [OBX_store_p, ctypes.POINTER(ctypes.c_char_p), ctypes.c_size_t])

# Client Credentials

# obx_err obx_sync_credentials(OBX_sync* sync, OBXSyncCredentialsType type, const void* data, size_t size);
obx_sync_credentials = c_fn_rc('obx_sync_credentials',
                               [OBX_sync_p, OBXSyncCredentialsType, ctypes.c_void_p, ctypes.c_size_t])

# obx_err obx_sync_credentials_user_password(OBX_sync* sync, OBXSyncCredentialsType type, const char* username, const char* password);
obx_sync_credentials_user_password = c_fn_rc('obx_sync_credentials_user_password',
                                               [OBX_sync_p, OBXSyncCredentialsType, ctypes.c_char_p,
                                                ctypes.c_char_p])

# obx_err obx_sync_credentials_add(OBX_sync* sync, OBXSyncCredentialsType type, const void* data, size_t size, bool complete);
obx_sync_credentials_add = c_fn_rc('obx_sync_credentials_add',
                                   [OBX_sync_p, OBXSyncCredentialsType, ctypes.c_void_p, ctypes.c_size_t, ctypes.c_bool])

# obx_err obx_sync_credentials_add_user_password(OBX_sync* sync, OBXSyncCredentialsType type, const char* username, const char* password, bool complete);
obx_sync_credentials_add_user_password = c_fn_rc('obx_sync_credentials_add_user_password',
                                                   [OBX_sync_p, OBXSyncCredentialsType, ctypes.c_char_p, ctypes.c_char_p,
                                                    ctypes.c_bool])

# Sync Control

# OBXSyncState obx_sync_state(OBX_sync* sync);
obx_sync_state = c_fn('obx_sync_state', OBXSyncState, [OBX_sync_p])

# obx_err obx_sync_request_updates_mode(OBX_sync* sync, OBXRequestUpdatesMode mode);
obx_sync_request_updates_mode = c_fn_rc('obx_sync_request_updates_mode', [OBX_sync_p, OBXRequestUpdatesMode])

# OBX_C_API obx_err obx_sync_updates_request(OBX_sync* sync, bool subscribe_for_pushes);
obx_sync_updates_request = c_fn_rc('obx_sync_updates_request', [OBX_sync_p, ctypes.c_bool])

# OBX_C_API obx_err obx_sync_updates_cancel(OBX_sync* sync);
obx_sync_updates_cancel = c_fn_rc('obx_sync_updates_cancel', [OBX_sync_p])

# obx_err obx_sync_start(OBX_sync* sync);
obx_sync_start = c_fn_rc('obx_sync_start', [OBX_sync_p])

# obx_err obx_sync_stop(OBX_sync* sync);
obx_sync_stop = c_fn_rc('obx_sync_stop', [OBX_sync_p])

# obx_err obx_sync_trigger_reconnect(OBX_sync* sync);
obx_sync_trigger_reconnect = c_fn_rc('obx_sync_trigger_reconnect', [OBX_sync_p])

# uint32_t obx_sync_protocol_version();
obx_sync_protocol_version = c_fn('obx_sync_protocol_version', ctypes.c_uint32, [])

# uint32_t obx_sync_protocol_version_server(OBX_sync* sync);
obx_sync_protocol_version_server = c_fn('obx_sync_protocol_version_server', ctypes.c_uint32, [OBX_sync_p])

# obx_err obx_sync_wait_for_logged_in_state(OBX_sync* sync, uint64_t timeout_millis);
obx_sync_wait_for_logged_in_state = c_fn_rc('obx_sync_wait_for_logged_in_state', [OBX_sync_p, ctypes.c_uint64])

# obx_err obx_sync_close(OBX_sync* sync);
obx_sync_close = c_fn_rc('obx_sync_close', [OBX_sync_p])

# Listener Callbacks

# void obx_sync_listener_connect(OBX_sync* sync, OBX_sync_listener_connect* listener, void* listener_arg);
obx_sync_listener_connect = c_fn('obx_sync_listener_connect', None, [OBX_sync_p, OBX_sync_listener_connect, ctypes.c_void_p])

# void obx_sync_listener_disconnect(OBX_sync* sync, OBX_sync_listener_disconnect* listener, void* listener_arg);
obx_sync_listener_disconnect = c_fn('obx_sync_listener_disconnect', None, [OBX_sync_p, OBX_sync_listener_disconnect, ctypes.c_void_p])

# void obx_sync_listener_login(OBX_sync* sync, OBX_sync_listener_login* listener, void* listener_arg);
obx_sync_listener_login = c_fn('obx_sync_listener_login', None, [OBX_sync_p, OBX_sync_listener_login, ctypes.c_void_p])

# void obx_sync_listener_login_failure(OBX_sync* sync, OBX_sync_listener_login_failure* listener, void* listener_arg);
obx_sync_listener_login_failure = c_fn('obx_sync_listener_login_failure', None, [OBX_sync_p, OBX_sync_listener_login_failure, ctypes.c_void_p])

# void obx_sync_listener_complete(OBX_sync* sync, OBX_sync_listener_complete* listener, void* listener_arg);
obx_sync_listener_error = c_fn('obx_sync_listener_error', None, [OBX_sync_p, OBX_sync_listener_error, ctypes.c_void_p])

# Filter Variables

# obx_err obx_sync_filter_variables_put(OBX_sync* sync, const char* name, const char* value);
obx_sync_filter_variables_put = c_fn_rc('obx_sync_filter_variables_put',
                                        [OBX_sync_p, c_char_p, c_char_p])

# obx_err obx_sync_filter_variables_remove(OBX_sync* sync, const char* name);
obx_sync_filter_variables_remove = c_fn_rc('obx_sync_filter_variables_remove',
                                           [OBX_sync_p, c_char_p])

# obx_err obx_sync_filter_variables_remove_all(OBX_sync* sync);
obx_sync_filter_variables_remove_all = c_fn_rc('obx_sync_filter_variables_remove_all',
                                               [OBX_sync_p])

# OBX_C_API obx_err obx_sync_outgoing_message_count(OBX_sync* sync, uint64_t limit, uint64_t* out_count);
obx_sync_outgoing_message_count = c_fn_rc('obx_sync_outgoing_message_count',
                                          [OBX_sync_p, ctypes.c_uint64, ctypes.POINTER(ctypes.c_uint64)])

OBXFeature = ctypes.c_int

class Feature(IntEnum):
    ResultArray = 1  # Functions that are returning multiple results (e.g. multiple objects) can be only used if this is available.
    TimeSeries = 2  # TimeSeries support (date/date-nano companion ID and other time-series functionality).
    Sync = 3  # Sync client availability. Visit https://objectbox.io/sync for more details.
    DebugLog = 4  # Check whether debug log can be enabled during runtime.
    Admin = 5  # Admin UI including a database browser, user management, and more. Depends on HttpServer (if Admin is available HttpServer is too).
    Tree = 6  # Tree with special GraphQL support
    SyncServer = 7  # Sync server availability. Visit https://objectbox.io/sync for more details.
    WebSockets = 8  # Implicitly added by Sync or SyncServer; disable via NoWebSockets
    Cluster = 9  # Sync Server has cluster functionality. Implicitly added by SyncServer; disable via NoCluster
    HttpServer = 10  # Embedded HTTP server.
    GraphQL = 11  # Embedded GraphQL server (via HTTP). Depends on HttpServer (if GraphQL is available HttpServer is too).
    Backup = 12  # Database Backup functionality; typically only enabled in Sync Server builds.
    Lmdb = 13  # The default database "provider"; writes data persistently to disk (ACID).
    VectorSearch = 14  # Vector search functionality; enables indexing for nearest neighbor search.
    Wal = 15  # WAL (write-ahead logging).
    SyncMongoDb = 16  # Sync connector to integrate MongoDB with SyncServer.
    Auth = 17  # Enables additional authentication/authorization methods for sync login, e.g.
    Trial = 18  # This is a free trial version; only applies to server builds (no trial builds for database and Sync clients).
    SyncFilters = 19  # Server-side filters to return individual data for each sync user (user-specific data).


# bool obx_has_feature(OBXFeature feature);
obx_has_feature = c_fn('obx_has_feature', ctypes.c_bool, [OBXFeature])
