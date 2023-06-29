from objectbox.model import *
from objectbox.model.properties import IndexType
import numpy as np
from datetime import datetime


@Entity(id=1, uid=1)
class TestEntity:
    id = Id(id=1, uid=1001)
    # TODO Enable indexing dynamically, e.g. have a constructor to enable index(es).
    #      E.g. indexString=False (defaults to false). Same for bytes.
    str = Property(str, id=2, uid=1002, index=True)
    bool = Property(bool, id=3, uid=1003)
    int64 = Property(int, type=PropertyType.long, id=4, uid=1004, index=True)
    int32 = Property(int, type=PropertyType.int, id=5, uid=1005, index=True, index_type=IndexType.hash)
    int16 = Property(int, type=PropertyType.short, id=6, uid=1006, index_type=IndexType.hash)
    int8 = Property(int, type=PropertyType.byte, id=7, uid=1007)
    float64 = Property(float, type=PropertyType.double, id=8, uid=1008)
    float32 = Property(float, type=PropertyType.float, id=9, uid=1009)
    bytes = Property(bytes, id=10, uid=1010, index_type=IndexType.hash64)
    ints = Property(np.ndarray, type=PropertyType.intVector, id=11, uid=1011)
    longs = Property(np.ndarray, type=PropertyType.longVector, id=12, uid=1012)
    floats = Property(np.ndarray, type=PropertyType.floatVector, id=13, uid=1013)
    doubles = Property(np.ndarray, type=PropertyType.doubleVector, id=14, uid=1014)
    ints_list = Property(list, type=PropertyType.intVector, id=15, uid=1015)
    longs_list = Property(list, type=PropertyType.longVector, id=16, uid=1016)
    floats_list = Property(list, type=PropertyType.floatVector, id=17, uid=1017)
    doubles_list = Property(list, type=PropertyType.doubleVector, id=18, uid=1018)
    date = Property(int, type=PropertyType.date, id=19, uid=1019)
    date_nano = Property(int, type=PropertyType.dateNano, id=20, uid=1020)
    transient = ""  # not "Property" so it's not stored

    def __init__(self, string: str = ""):
        self.str = string


@Entity(id=2, uid=2)
class TestEntityDatetime:
    id = Id(id=1, uid=2001)
    date = Property(datetime, type=PropertyType.date, id=2, uid=2002)
    date_nano = Property(datetime, type=PropertyType.dateNano, id=3, uid=2003)

    def __init__(self, string: str = ""):
        self.str = string
