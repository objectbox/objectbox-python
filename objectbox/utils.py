import numpy as np

from objectbox.c import *
from objectbox.model.properties import VectorDistanceType


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
