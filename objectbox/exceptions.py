from typing import Dict, Optional, Type

from objectbox.c import py_str, C, DbErrorCode


class DbError(Exception):
    """The base class for all exceptions thrown by ObjectBox.
    Every exception has a code attribute for identification.

    Some also derive from the matching built-in exception, e.g. IllegalArgumentError is a ValueError."""

    code = DbErrorCode.OBX_NO_SUCCESS  # Re-defined by derived classes

    def __init__(self, message: Optional[str] = None):
        """Creates the exception with the given message, or by default the last error message of the C library."""
        self.message = message if message is not None else py_str(C.obx_last_error_message())
        code = self.code
        label = f"{code.value} ({code.name})" if isinstance(code, DbErrorCode) else str(code)
        super().__init__(f"{label} - {self.message}")

    @staticmethod
    def from_code(code: int):
        """Creates a DbError of the given error code."""
        return create_db_error(code)

    @staticmethod
    def last():
        """Creates a DbError of the last error that was generated in core."""
        return DbError.from_code(C.obx_last_error())


class NotFoundError(DbError):
    """Raised when an object is not found."""
    code = DbErrorCode.OBX_NOT_FOUND


class NoSuccessError(DbError):
    code = DbErrorCode.OBX_NO_SUCCESS


class TimeoutError(DbError):
    code = DbErrorCode.OBX_TIMEOUT


class IllegalStateError(DbError, RuntimeError):
    """An operation is not allowed in the current state, e.g. on a closed object (also a RuntimeError)."""
    code = DbErrorCode.OBX_ERROR_ILLEGAL_STATE


class IllegalArgumentError(DbError, ValueError):
    """An argument has an invalid value (also a ValueError)."""
    code = DbErrorCode.OBX_ERROR_ILLEGAL_ARGUMENT


class AllocationError(DbError):
    code = DbErrorCode.OBX_ERROR_ALLOCATION


class NumericOverflowError(DbError):
    code = DbErrorCode.OBX_ERROR_NUMERIC_OVERFLOW


class FeatureNotAvailable(DbError, RuntimeError):
    """The feature is not available in the loaded ObjectBox library (also a RuntimeError)."""
    code = DbErrorCode.OBX_ERROR_FEATURE_NOT_AVAILABLE


class ShuttingDownError(DbError):
    code = DbErrorCode.OBX_ERROR_SHUTTING_DOWN


class IoError(DbError):
    code = DbErrorCode.OBX_ERROR_IO


class BackupFileInvalidError(DbError):
    code = DbErrorCode.OBX_ERROR_BACKUP_FILE_INVALID


class NoErrorInfoError(DbError):
    code = DbErrorCode.OBX_ERROR_NO_ERROR_INFO


class GeneralError(DbError):
    code = DbErrorCode.OBX_ERROR_GENERAL


class UnknownError(DbError):
    code = DbErrorCode.OBX_ERROR_UNKNOWN


class DbFullError(DbError):
    code = DbErrorCode.OBX_ERROR_DB_FULL


class MaxReadersExceededError(DbError):
    code = DbErrorCode.OBX_ERROR_MAX_READERS_EXCEEDED


class StoreMustShutdownError(DbError):
    code = DbErrorCode.OBX_ERROR_STORE_MUST_SHUTDOWN


class MaxDataSizeExceededError(DbError):
    code = DbErrorCode.OBX_ERROR_MAX_DATA_SIZE_EXCEEDED


class DbGeneralError(DbError):
    code = DbErrorCode.OBX_ERROR_DB_GENERAL


class GeneralStorageError(DbError):
    code = DbErrorCode.OBX_ERROR_STORAGE_GENERAL


class UniqueViolatedError(DbError):
    code = DbErrorCode.OBX_ERROR_UNIQUE_VIOLATED


class NonUniqueResultError(DbError):
    code = DbErrorCode.OBX_ERROR_NON_UNIQUE_RESULT


class PropertyTypeMismatchError(DbError):
    code = DbErrorCode.OBX_ERROR_PROPERTY_TYPE_MISMATCH


class IdAlreadyExistsError(DbError):
    code = DbErrorCode.OBX_ERROR_ID_ALREADY_EXISTS


class IdNotFoundError(DbError):
    code = DbErrorCode.OBX_ERROR_ID_NOT_FOUND


class TimeSeriesError(DbError):
    code = DbErrorCode.OBX_ERROR_TIME_SERIES


class ConstraintViolatedError(DbError):
    code = DbErrorCode.OBX_ERROR_CONSTRAINT_VIOLATED


class StdIllegalArgumentError(DbError):
    code = DbErrorCode.OBX_ERROR_STD_ILLEGAL_ARGUMENT


class StdOutOfRangeError(DbError):
    code = DbErrorCode.OBX_ERROR_STD_OUT_OF_RANGE


class StdLengthError(DbError):
    code = DbErrorCode.OBX_ERROR_STD_LENGTH


class StdBadAllocError(DbError):
    code = DbErrorCode.OBX_ERROR_STD_BAD_ALLOC


class StdRangeError(DbError):
    code = DbErrorCode.OBX_ERROR_STD_RANGE


class StdOverflowError(DbError):
    code = DbErrorCode.OBX_ERROR_STD_OVERFLOW


class StdOtherError(DbError):
    code = DbErrorCode.OBX_ERROR_STD_OTHER


class SchemaError(DbError):
    code = DbErrorCode.OBX_ERROR_SCHEMA


class FileCorruptError(DbError):
    code = DbErrorCode.OBX_ERROR_FILE_CORRUPT


class FilePagesCorruptError(DbError):
    code = DbErrorCode.OBX_ERROR_FILE_PAGES_CORRUPT


class SchemaObjectNotFoundError(DbError):
    code = DbErrorCode.OBX_ERROR_SCHEMA_OBJECT_NOT_FOUND


class TreeModelInvalidError(DbError):
    code = DbErrorCode.OBX_ERROR_TREE_MODEL_INVALID


class TreeValueTypeMismatchError(DbError):
    code = DbErrorCode.OBX_ERROR_TREE_VALUE_TYPE_MISMATCH


class TreePathNonUniqueError(DbError):
    code = DbErrorCode.OBX_ERROR_TREE_PATH_NON_UNIQUE


class TreePathIllegalError(DbError):
    code = DbErrorCode.OBX_ERROR_TREE_PATH_ILLEGAL


class TreeOtherError(DbError):
    code = DbErrorCode.OBX_ERROR_TREE_OTHER


obx_db_error_map: Dict[int, Type] = {}


def _init_db_errror_map():
    for subclass in DbError.__subclasses__():
        obx_db_error_map[subclass.code] = subclass


_init_db_errror_map()


def create_db_error(code: int) -> DbError:
    if code == DbErrorCode.OBX_SUCCESS:
        raise ValueError("Can't create a DbError for code: OBX_SUCCESS")
    error_class = obx_db_error_map.get(code)
    if error_class is None:  # E.g. a code of a newer C library: a DbError with that code
        error = DbError.__new__(DbError)
        error.code = DbErrorCode(code) if code in DbErrorCode._value2member_map_ else code
        DbError.__init__(error)
        return error
    return error_class()
