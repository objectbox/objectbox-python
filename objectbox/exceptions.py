from typing import Dict, Type

from objectbox.c import py_str, C, StorageErrorCode


class ObjectBoxException(Exception):
    """The base class for all exceptions thrown by ObjectBox."""

    def __init__(self, message: str):
        super().__init__(message)


class StorageException(ObjectBoxException):
    """The base class for all exceptions thrown by ObjectBox core.
    Every exception has a code attribute for identification."""

    code = StorageErrorCode.OBX_NO_SUCCESS  # Re-defined by derived classes

    def __init__(self):
        self.message = py_str(C.obx_last_error_message())
        super().__init__("%d (%s) - %s" % (self.code.value, self.code.name, self.message))

    @staticmethod
    def from_code(code: int):
        """Creates a StorageException of the given error code."""
        return create_storage_exception(code)

    @staticmethod
    def last():
        """Creates a StorageException of the last error that was generated in core."""
        return StorageException.from_code(C.obx_last_error())


class NotFoundException(StorageException):
    """Raised when an object is not found."""
    code = StorageErrorCode.OBX_NOT_FOUND


class NoSuccessException(StorageException):
    code = StorageErrorCode.OBX_NO_SUCCESS


class TimeoutException(StorageException):
    code = StorageErrorCode.OBX_TIMEOUT


class IllegalStateError(StorageException):
    code = StorageErrorCode.OBX_ERROR_ILLEGAL_STATE


class IllegalArgumentError(StorageException):
    code = StorageErrorCode.OBX_ERROR_ILLEGAL_ARGUMENT


class AllocationError(StorageException):
    code = StorageErrorCode.OBX_ERROR_ALLOCATION


class NumericOverflowError(StorageException):
    code = StorageErrorCode.OBX_ERROR_NUMERIC_OVERFLOW


class FeatureNotAvailable(StorageException):
    code = StorageErrorCode.OBX_ERROR_FEATURE_NOT_AVAILABLE


class ShuttingDownError(StorageException):
    code = StorageErrorCode.OBX_ERROR_SHUTTING_DOWN


class IoError(StorageException):
    code = StorageErrorCode.OBX_ERROR_IO


class BackupFileInvalidError(StorageException):
    code = StorageErrorCode.OBX_ERROR_BACKUP_FILE_INVALID


class NoErrorInfoError(StorageException):
    code = StorageErrorCode.OBX_ERROR_NO_ERROR_INFO


class GeneralError(StorageException):
    code = StorageErrorCode.OBX_ERROR_GENERAL


class UnknownError(StorageException):
    code = StorageErrorCode.OBX_ERROR_UNKNOWN


class DbFullError(StorageException):
    code = StorageErrorCode.OBX_ERROR_DB_FULL


class MaxReadersExceededError(StorageException):
    code = StorageErrorCode.OBX_ERROR_MAX_READERS_EXCEEDED


class StoreMustShutdownError(StorageException):
    code = StorageErrorCode.OBX_ERROR_STORE_MUST_SHUTDOWN


class MaxDataSizeExceededError(StorageException):
    code = StorageErrorCode.OBX_ERROR_MAX_DATA_SIZE_EXCEEDED


class DbGeneralError(StorageException):
    code = StorageErrorCode.OBX_ERROR_DB_GENERAL


class StorageGeneralError(StorageException):
    code = StorageErrorCode.OBX_ERROR_STORAGE_GENERAL


class UniqueViolatedError(StorageException):
    code = StorageErrorCode.OBX_ERROR_UNIQUE_VIOLATED


class NonUniqueResultError(StorageException):
    code = StorageErrorCode.OBX_ERROR_NON_UNIQUE_RESULT


class PropertyTypeMismatchError(StorageException):
    code = StorageErrorCode.OBX_ERROR_PROPERTY_TYPE_MISMATCH


class IdAlreadyExistsError(StorageException):
    code = StorageErrorCode.OBX_ERROR_ID_ALREADY_EXISTS


class IdNotFoundError(StorageException):
    code = StorageErrorCode.OBX_ERROR_ID_NOT_FOUND


class TimeSeriesError(StorageException):
    code = StorageErrorCode.OBX_ERROR_TIME_SERIES


class ConstraintViolatedError(StorageException):
    code = StorageErrorCode.OBX_ERROR_CONSTRAINT_VIOLATED


class StdIllegalArgumentError(StorageException):
    code = StorageErrorCode.OBX_ERROR_STD_ILLEGAL_ARGUMENT


class StdOutOfRangeError(StorageException):
    code = StorageErrorCode.OBX_ERROR_STD_OUT_OF_RANGE


class StdLengthError(StorageException):
    code = StorageErrorCode.OBX_ERROR_STD_LENGTH


class StdBadAllocError(StorageException):
    code = StorageErrorCode.OBX_ERROR_STD_BAD_ALLOC


class StdRangeError(StorageException):
    code = StorageErrorCode.OBX_ERROR_STD_RANGE


class StdOverflowError(StorageException):
    code = StorageErrorCode.OBX_ERROR_STD_OVERFLOW


class StdOtherError(StorageException):
    code = StorageErrorCode.OBX_ERROR_STD_OTHER


class SchemaError(StorageException):
    code = StorageErrorCode.OBX_ERROR_SCHEMA


class FileCorruptError(StorageException):
    code = StorageErrorCode.OBX_ERROR_FILE_CORRUPT


class FilePagesCorruptError(StorageException):
    code = StorageErrorCode.OBX_ERROR_FILE_PAGES_CORRUPT


class SchemaObjectNotFoundError(StorageException):
    code = StorageErrorCode.OBX_ERROR_SCHEMA_OBJECT_NOT_FOUND


class TreeModelInvalidError(StorageException):
    code = StorageErrorCode.OBX_ERROR_TREE_MODEL_INVALID


class TreeValueTypeMismatchError(StorageException):
    code = StorageErrorCode.OBX_ERROR_TREE_VALUE_TYPE_MISMATCH


class TreePathNonUniqueError(StorageException):
    code = StorageErrorCode.OBX_ERROR_TREE_PATH_NON_UNIQUE


class TreePathIllegalError(StorageException):
    code = StorageErrorCode.OBX_ERROR_TREE_PATH_ILLEGAL


class TreeOtherError(StorageException):
    code = StorageErrorCode.OBX_ERROR_TREE_OTHER


obx_storage_exceptions_map: Dict[int, Type] = {}


def _init_storage_exceptions_map():
    for subclass in StorageException.__subclasses__():
        obx_storage_exceptions_map[subclass.code] = subclass


_init_storage_exceptions_map()


def create_storage_exception(code: int) -> StorageException:
    if code == StorageErrorCode.OBX_SUCCESS:
        raise Exception(f"Can't create a StorageException for code: OBX_SUCCESS")
    elif code not in obx_storage_exceptions_map:
        raise Exception(f"Unrecognized StorageException code: {code}")
    return obx_storage_exceptions_map[code]()
