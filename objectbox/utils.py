import numpy as np

from objectbox.c import *
from objectbox.model.properties import VectorDistanceType
from datetime import datetime, timezone

def check_float_vector(vector: Union[np.ndarray, List[float]], vector_name: str):
    """ Checks that the given vector is a float vector (either np.ndarray or Python's list). """
    if isinstance(vector, np.ndarray) and vector.dtype != np.float32:
        raise Exception(f"{vector_name} dtype is expected to be np.float32, got: {vector.dtype}")
    elif isinstance(vector, list) and len(vector) > 0 and (type(vector[0]) is not float):
        raise Exception(f"{vector_name} is expected to be a float list, got vector[0]: {type(vector[0])}")


def vector_distance_f32(distance_type: VectorDistanceType,
                        vector1: Union[np.ndarray, List[float]],
                        vector2: Union[np.ndarray, List[float]],
                        dimension: int) -> float:
    """ Utility function to calculate the distance of two vectors. """
    check_float_vector(vector1, "vector1")
    check_float_vector(vector2, "vector2")
    return obx_vector_distance_float32(distance_type,
                                       c_array(vector1, ctypes.c_float),
                                       c_array(vector2, ctypes.c_float),
                                       dimension)


def vector_distance_to_relevance(distance_type: VectorDistanceType, distance: float) -> float:
    """ Converts the given distance to a relevance score in range [0.0, 1.0], according to its type. """
    return obx_vector_distance_to_relevance(distance_type, distance)

def date_value_to_int(value, multiplier: int) -> int:
    if isinstance(value, datetime):
        try:
            return round(value.timestamp() * multiplier)  # timestamp returns seconds
        except OSError:
            # On Windows, timestamp() raises an OSError for naive datetime objects with dates is close to the epoch.
            # Thus, it is highly recommended to only use datetime *with* timezone information (no issue here).
            # See bug reports:
            # https://github.com/python/cpython/issues/81708 and https://github.com/python/cpython/issues/94414
            # The workaround is to go via timezone-aware datetime objects, which seem to work - with one caveat.
            local_tz = datetime.now().astimezone().tzinfo
            value = value.replace(tzinfo=local_tz)
            value = value.astimezone(timezone.utc)
            # Caveat: times may be off by; offset should be 0 but actually was seen at -3600 in CEST (Linux & Win).
            # See also https://stackoverflow.com/q/56931738/551269
            # So, let's check value 0 as a reference and use the resulting timestamp as an offset for correction.
            offset = datetime.fromtimestamp(0).replace(tzinfo=local_tz).astimezone(timezone.utc).timestamp()
            return round((value.timestamp() - offset) * multiplier)  # timestamp returns seconds
    elif isinstance(value, float):
        return round(value * multiplier)  # floats typically represent seconds
    elif isinstance(value, int):  # Interpret ints as-is (without the multiplier); e.g. milliseconds or nanoseconds
        return value
    else:
        raise TypeError(
            f"Unsupported Python datetime type: {type(value)}. Please use datetime, float (seconds based) or "
            f"int (milliseconds for Date, nanoseconds for DateNano).")
