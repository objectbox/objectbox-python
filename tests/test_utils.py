from datetime import timezone, datetime, timedelta

import pytest

from objectbox.model.entity import _Entity
from objectbox.utils import *


def test_date_value_to_int__basics():
    assert _Entity.date_value_to_int(1234, 1000) == 1234
    assert _Entity.date_value_to_int(1234, 1000000000) == 1234
    assert _Entity.date_value_to_int(1234.0, 1000) == 1234000  # milliseconds
    assert _Entity.date_value_to_int(1234.0, 1000000000) == 1234000000000  # nanoseconds
    assert _Entity.date_value_to_int(datetime.fromtimestamp(1234), 1000) == 1234000  # milliseconds


def test_date_value_to_int__timezone():
    # create datetime object for may 1st, 2000
    dt_utc = datetime(year=2000, month=5, day=1, hour=12, minute=30, second=45, microsecond=123456, tzinfo=timezone.utc)
    dt_plus2 = datetime(year=2000, month=5, day=1, hour=14, minute=30, second=45, microsecond=123456,
                        tzinfo=timezone(offset=timedelta(hours=2)))

    # Demonstrate Python's semantic
    assert dt_utc == dt_plus2
    assert dt_utc.timestamp() == dt_plus2.timestamp()

    # Actual test
    expected: int = 957184245123
    assert _Entity.date_value_to_int(dt_utc, 1000) == expected
    assert _Entity.date_value_to_int(dt_plus2, 1000) == expected


def test_date_value_to_int__naive():
    dt_naive = datetime(year=2000, month=5, day=1, hour=12, minute=30, second=45, microsecond=123456)
    local_tz = datetime.now().astimezone().tzinfo
    dt_local = datetime(year=2000, month=5, day=1, hour=12, minute=30, second=45, microsecond=123456, tzinfo=local_tz)

    # Demonstrate Python's semantic
    assert dt_naive.astimezone(timezone.utc) == dt_local  # naive lacks the TZ, so we can't compare directly
    assert dt_naive.timestamp() == dt_local.timestamp()

    # Actual test
    assert _Entity.date_value_to_int(dt_naive, 1000) == _Entity.date_value_to_int(dt_local, 1000)


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
