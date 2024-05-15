import pytest

from objectbox.utils import *


def test_vector_distance_f32():
    """ Tests distance values between two vectors. """

    a = np.array([3.4, 2.9, -10, 1.0], dtype=np.float32)
    b = np.array([56., -1.2, 22, 2.0], dtype=np.float32)

    a_norm = a / np.linalg.norm(a)
    b_norm = b / np.linalg.norm(b)

    assert vector_distance_f32(VectorDistanceType.EUCLIDEAN, a, b, 4) == pytest.approx(np.dot(b - a, b - a))
    assert vector_distance_f32(VectorDistanceType.COSINE, a, b, 4) == pytest.approx(1.0469311)
    assert vector_distance_f32(VectorDistanceType.DOT_PRODUCT, a_norm, b_norm, 4) == pytest.approx(1.0469311)
    assert vector_distance_f32(VectorDistanceType.DOT_PRODUCT_NON_NORMALIZED, a, b, 4) == pytest.approx(1.519307)
