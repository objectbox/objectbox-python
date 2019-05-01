import ctypes.util

# initialize the C library
C = ctypes.CDLL(ctypes.util.find_library("objectbox"))

# define some basic types
obx_err = ctypes.c_int
obx_schema_id = ctypes.c_uint32
obx_uid = ctypes.c_uint64
obx_id = ctypes.c_uint64
obx_qb_cond = ctypes.c_int

# enums
OBXPropertyType = ctypes.c_int
OBXPropertyFlags = ctypes.c_int
OBXDebugFlags = ctypes.c_int
OBXPutMode = ctypes.c_int
OBXOrderFlags = ctypes.c_int


class OBX_model(ctypes.Structure):
    pass


OBX_model_p = ctypes.POINTER(OBX_model)


class OBX_store(ctypes.Structure):
    pass


OBX_store_p = ctypes.POINTER(OBX_store)


class OBX_store_options(ctypes.Structure):
    _fields_ = [
        ('directory', ctypes.c_char_p),
        ('maxDbSizeInKByte', ctypes.c_uint64),
        ('fileMode', ctypes.c_uint),
        ('maxReaders', ctypes.c_uint)
    ]


OBX_store_options_p = ctypes.POINTER(OBX_store_options)


class OBX_bytes(ctypes.Structure):
    _fields_ = [
        ('data', ctypes.c_void_p),
        ('size', ctypes.c_size_t),
    ]


OBX_bytes_p = ctypes.POINTER(OBX_bytes)


class OBX_bytes_array(ctypes.Structure):
    _fields_ = [
        ('data', ctypes.POINTER(OBX_bytes)),
        ('count', ctypes.c_size_t),
    ]


OBX_bytes_array_p = ctypes.POINTER(OBX_bytes_array)


class OBX_id_array(ctypes.Structure):
    _fields_ = [
        ('ids', ctypes.POINTER(obx_id)),
        ('count', ctypes.c_size_t),
    ]


OBX_id_array_p = ctypes.POINTER(OBX_id_array)


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


class CError(Exception):
    def __init__(self, code):
        self.code = code
        self.message = ctypes.c_char_p(C.obx_last_error_message()).value.decode("utf8")
        super(CError, self).__init__(self.message)


# check obx_err and raise an error
def errcheck(code: obx_err, func, args):
    if code != 0:
        raise CError(code)


# creates a global function "name" with the given restype & argtypes, calling C function with the same name
def fn(name: str, restype: type, argtypes):
    func = C.__getattr__(name)

    if restype == obx_err:
        func.errcheck = errcheck
    else:
        func.restype = restype

    func.argtypes = argtypes
    return func


def c_str(string: str) -> ctypes.c_char_p:
    return string.encode('utf-8')


# OBX_model* (void);
obx_model_create = fn('obx_model_create', OBX_model_p, [])

# obx_err (OBX_model* model, const char* name, obx_schema_id entity_id, obx_uid entity_uid);
obx_model_entity = fn('obx_model_entity', obx_err, [OBX_model_p, ctypes.c_char_p, obx_schema_id, obx_uid])

# obx_err (OBX_model* model, const char* name, OBXPropertyType type, obx_schema_id property_id, obx_uid property_uid);
obx_model_property = fn('obx_model_property', obx_err,
                        [OBX_model_p, ctypes.c_char_p, OBXPropertyType, obx_schema_id, obx_uid])

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
OBXPropertyType_ByteVector = 23
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

OBXDebugFlags_LOG_TRANSACTIONS_READ = 1,
OBXDebugFlags_LOG_TRANSACTIONS_WRITE = 2,
OBXDebugFlags_LOG_QUERIES = 4,
OBXDebugFlags_LOG_QUERY_PARAMETERS = 8,
OBXDebugFlags_LOG_ASYNC_QUEUE = 16,


# Standard put ("insert or update")
OBXPutMode_PUT = 1,

# Put succeeds only if the entity does not exist yet.
OBXPutMode_INSERT = 2,

# Put succeeds only if the entity already exist.
OBXPutMode_UPDATE = 3,

# The given ID (non-zero) is guaranteed to be new; don't use unless you know exactly what you are doing!
# This is primarily used internally. Wrong usage leads to inconsistent data (e.g. index data not updated)!
OBXPutMode_PUT_ID_GUARANTEED_TO_BE_NEW = 4


# Reverts the order from ascending (default) to descending.
OBXOrderFlags_DESCENDING = 1,

# Makes upper case letters (e.g. "Z") be sorted before lower case letters (e.g. "a").
# If not specified, the default is case insensitive for ASCII characters.
OBXOrderFlags_CASE_SENSITIVE = 2,

# For scalars only: changes the comparison to unsigned (default is signed).
OBXOrderFlags_UNSIGNED = 4,

# null values will be put last.
# If not specified, by default null values will be put first.
OBXOrderFlags_NULLS_LAST = 8,

# null values should be treated equal to zero (scalars only).
OBXOrderFlags_NULLS_ZERO = 16,
