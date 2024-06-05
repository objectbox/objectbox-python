from typing import Dict, Type

from objectbox.c import CoreException, CoreExceptionCode


class NotFoundException(CoreException):
    """Raised when an object is not found."""
    code = CoreExceptionCode.OBX_NOT_FOUND


class NoSuccessException(CoreException):
    code = CoreExceptionCode.OBX_NO_SUCCESS


class TimeoutException(CoreException):
    code = CoreExceptionCode.OBX_TIMEOUT


class IllegalStateError(CoreException):
    code = CoreExceptionCode.OBX_ERROR_ILLEGAL_STATE


class IllegalArgumentError(CoreException):
    code = CoreExceptionCode.OBX_ERROR_ILLEGAL_ARGUMENT


class AllocationError(CoreException):
    code = CoreExceptionCode.OBX_ERROR_ALLOCATION


class NumericOverflowError(CoreException):
    code = CoreExceptionCode.OBX_ERROR_NUMERIC_OVERFLOW


class FeatureNotAvailable(CoreException):
    code = CoreExceptionCode.OBX_ERROR_FEATURE_NOT_AVAILABLE


class ShuttingDownError(CoreException):
    code = CoreExceptionCode.OBX_ERROR_SHUTTING_DOWN


class IoError(CoreException):
    code = CoreExceptionCode.OBX_ERROR_IO


class BackupFileInvalidError(CoreException):
    code = CoreExceptionCode.OBX_ERROR_BACKUP_FILE_INVALID


class NoErrorInfoError(CoreException):
    code = CoreExceptionCode.OBX_ERROR_NO_ERROR_INFO


class GeneralError(CoreException):
    code = CoreExceptionCode.OBX_ERROR_GENERAL


class UnknownError(CoreException):
    code = CoreExceptionCode.OBX_ERROR_UNKNOWN


class DbFullError(CoreException):
    code = CoreExceptionCode.OBX_ERROR_DB_FULL


class MaxReadersExceededError(CoreException):
    code = CoreExceptionCode.OBX_ERROR_MAX_READERS_EXCEEDED


class StoreMustShutdownError(CoreException):
    code = CoreExceptionCode.OBX_ERROR_STORE_MUST_SHUTDOWN


class MaxDataSizeExceededError(CoreException):
    code = CoreExceptionCode.OBX_ERROR_MAX_DATA_SIZE_EXCEEDED


class DbGeneralError(CoreException):
    code = CoreExceptionCode.OBX_ERROR_DB_GENERAL


class StorageGeneralError(CoreException):
    code = CoreExceptionCode.OBX_ERROR_STORAGE_GENERAL


class UniqueViolatedError(CoreException):
    code = CoreExceptionCode.OBX_ERROR_UNIQUE_VIOLATED


class NonUniqueResultError(CoreException):
    code = CoreExceptionCode.OBX_ERROR_NON_UNIQUE_RESULT


class PropertyTypeMismatchError(CoreException):
    code = CoreExceptionCode.OBX_ERROR_PROPERTY_TYPE_MISMATCH


class IdAlreadyExistsError(CoreException):
    code = CoreExceptionCode.OBX_ERROR_ID_ALREADY_EXISTS


class IdNotFoundError(CoreException):
    code = CoreExceptionCode.OBX_ERROR_ID_NOT_FOUND


class TimeSeriesError(CoreException):
    code = CoreExceptionCode.OBX_ERROR_TIME_SERIES


class ConstraintViolatedError(CoreException):
    code = CoreExceptionCode.OBX_ERROR_CONSTRAINT_VIOLATED


class StdIllegalArgumentError(CoreException):
    code = CoreExceptionCode.OBX_ERROR_STD_ILLEGAL_ARGUMENT


class StdOutOfRangeError(CoreException):
    code = CoreExceptionCode.OBX_ERROR_STD_OUT_OF_RANGE


class StdLengthError(CoreException):
    code = CoreExceptionCode.OBX_ERROR_STD_LENGTH


class StdBadAllocError(CoreException):
    code = CoreExceptionCode.OBX_ERROR_STD_BAD_ALLOC


class StdRangeError(CoreException):
    code = CoreExceptionCode.OBX_ERROR_STD_RANGE


class StdOverflowError(CoreException):
    code = CoreExceptionCode.OBX_ERROR_STD_OVERFLOW


class StdOtherError(CoreException):
    code = CoreExceptionCode.OBX_ERROR_STD_OTHER


class SchemaError(CoreException):
    code = CoreExceptionCode.OBX_ERROR_SCHEMA


class FileCorruptError(CoreException):
    code = CoreExceptionCode.OBX_ERROR_FILE_CORRUPT


class FilePagesCorruptError(CoreException):
    code = CoreExceptionCode.OBX_ERROR_FILE_PAGES_CORRUPT


class SchemaObjectNotFoundError(CoreException):
    code = CoreExceptionCode.OBX_ERROR_SCHEMA_OBJECT_NOT_FOUND


class TreeModelInvalidError(CoreException):
    code = CoreExceptionCode.OBX_ERROR_TREE_MODEL_INVALID


class TreeValueTypeMismatchError(CoreException):
    code = CoreExceptionCode.OBX_ERROR_TREE_VALUE_TYPE_MISMATCH


class TreePathNonUniqueError(CoreException):
    code = CoreExceptionCode.OBX_ERROR_TREE_PATH_NON_UNIQUE


class TreePathIllegalError(CoreException):
    code = CoreExceptionCode.OBX_ERROR_TREE_PATH_ILLEGAL


class TreeOtherError(CoreException):
    code = CoreExceptionCode.OBX_ERROR_TREE_OTHER


obx_core_exceptions_map: Dict[int, Type] = {}


def _init_core_exceptions_map():
    import inspect
    import sys

    def is_core_exception_subclass(element_) -> bool:
        valid = True
        valid &= inspect.isclass(element_)
        valid &= hasattr(element_, "code")
        return valid

    this_module = sys.modules[__name__]
    for name, element in inspect.getmembers(this_module):
        if is_core_exception_subclass(element):
            obx_core_exceptions_map[element.code] = element


_init_core_exceptions_map()


def create_core_exception(code: int) -> CoreException:
    if code == CoreExceptionCode.OBX_SUCCESS:
        raise Exception(f"Can't create a CoreException for code: OBX_SUCCESS")
    elif code not in obx_core_exceptions_map:
        raise Exception(f"Unrecognized CoreException code: {code}")
    return obx_core_exceptions_map[code]()
