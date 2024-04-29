from objectbox.model import *
from objectbox.model.properties import *
import numpy as np
from datetime import datetime
from typing import Generic, Dict, Any


@Entity(id=1, uid=1)
class TestEntity:
    id = Id(id=1, uid=1001)
    # TODO Enable indexing dynamically, e.g. have a constructor to enable index(es).
    #      E.g. indexString=False (defaults to false). Same for bytes.
    # TODO Test HASH and HASH64 indices (only supported for strings)
    str = Property(str, id=2, uid=1002, index=Index(id=1, uid=10001))
    bool = Property(bool, id=3, uid=1003)
    int64 = Property(int, type=PropertyType.long, id=4, uid=1004, index=Index(id=2, uid=10002))
    int32 = Property(int, type=PropertyType.int, id=5, uid=1005)
    int16 = Property(int, type=PropertyType.short, id=6, uid=1006)
    int8 = Property(int, type=PropertyType.byte, id=7, uid=1007)
    float64 = Property(float, type=PropertyType.double, id=8, uid=1008)
    float32 = Property(float, type=PropertyType.float, id=9, uid=1009)
    bools = Property(np.ndarray, type=PropertyType.boolVector, id=10, uid=1010)
    bytes = Property(bytes, id=11, uid=1011)
    shorts = Property(np.ndarray, type=PropertyType.shortVector, id=12, uid=1012)
    chars = Property(np.ndarray, type=PropertyType.charVector, id=13, uid=1013)
    ints = Property(np.ndarray, type=PropertyType.intVector, id=14, uid=1014)
    longs = Property(np.ndarray, type=PropertyType.longVector, id=15, uid=1015)
    floats = Property(np.ndarray, type=PropertyType.floatVector, id=16, uid=1016)
    doubles = Property(np.ndarray, type=PropertyType.doubleVector, id=17, uid=1017)
    bools_list = Property(list, type=PropertyType.boolVector, id=18, uid=1018)
    shorts_list = Property(list, type=PropertyType.shortVector, id=19, uid=1019)
    chars_list = Property(list, type=PropertyType.charVector, id=20, uid=1020)
    ints_list = Property(list, type=PropertyType.intVector, id=21, uid=1021)
    longs_list = Property(list, type=PropertyType.longVector, id=22, uid=1022)
    floats_list = Property(list, type=PropertyType.floatVector, id=23, uid=1023)
    doubles_list = Property(list, type=PropertyType.doubleVector, id=24, uid=1024)
    date = Property(int, type=PropertyType.date, id=25, uid=1025)
    date_nano = Property(int, type=PropertyType.dateNano, id=26, uid=1026)
    flex = Property(Generic, type=PropertyType.flex, id=27, uid=1027)
    transient = ""  # not "Property" so it's not stored


@Entity(id=2, uid=2)
class TestEntityDatetime:
    id = Id(id=1, uid=2001)
    date = Property(datetime, type=PropertyType.date, id=2, uid=2002)
    date_nano = Property(datetime, type=PropertyType.dateNano, id=3, uid=2003)


@Entity(id=3, uid=3)
class TestEntityFlex:
    id = Id(id=1, uid=3001)
    flex = Property(Any, type=PropertyType.flex, id=2, uid=3002)


@Entity(id=4, uid=4)
class VectorEntity:
    id = Id(id=1, uid=4001)
    name = Property(str, type=PropertyType.string, id=2, uid=4002)
    vector = Property(np.ndarray, type=PropertyType.floatVector, id=3, uid=4003,
                      index=HnswIndex(
                          id=3, uid=40001,
                          dimensions=2, distance_type=HnswDistanceType.EUCLIDEAN)
                      )
