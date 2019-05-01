import ctypes.util

# initialize the C library
C = ctypes.CDLL(ctypes.util.find_library("objectbox"))

# define some basic types
obx_err = ctypes.c_int
obx_schema_id = ctypes.c_uint32
obx_uid = ctypes.c_uint64
obx_id = ctypes.c_uint64
obx_qb_cond = ctypes.c_int


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


# creates a global function "name" with the given restype & argtypes, calling C function with the same name
def fn(name: str, restype: type, argtypes):
    func = C.__getattr__(name)

    if restype == obx_err:
        # TODO func.errcheck
        pass
    else:
        func.restype = restype

    func.argtypes = argtypes
    return func


# OBX_model* obx_model_create(void);
obx_model_create = fn('obx_model_create', OBX_model_p, [])

# obx_err obx_model_entity(OBX_model* model, const char* name, obx_schema_id entity_id, obx_uid entity_uid);
obx_model_entity = fn('obx_model_entity', obx_err, [OBX_model_p, ctypes.c_char_p, obx_schema_id, obx_uid])
