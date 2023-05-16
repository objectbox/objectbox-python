from objectbox.model import *
import numpy as np


@Entity(id=1, uid=1)
class TestEntity:
    id = Id(id=1, uid=1001)
    str = Property(str, id=2, uid=1002)
    bool = Property(bool, id=3, uid=1003)
    int64 = Property(int, type=PropertyType.long, id=4, uid=1004)
    int32 = Property(int, type=PropertyType.int, id=5, uid=1005)
    int16 = Property(int, type=PropertyType.short, id=6, uid=1006)
    int8 = Property(int, type=PropertyType.byte, id=7, uid=1007)
    float64 = Property(float, type=PropertyType.double, id=8, uid=1008)
    float32 = Property(float, type=PropertyType.float, id=9, uid=1009)
    bytes = Property(bytes, id=10, uid=1010)
    ints = Property(np.ndarray, type=PropertyType.intVector, id=11, uid=1011)
    longs = Property(np.ndarray, type=PropertyType.longVector, id=12, uid=1012)
    floats = Property(np.ndarray, type=PropertyType.floatVector, id=13, uid=1013)
    doubles = Property(np.ndarray, type=PropertyType.doubleVector, id=14, uid=1014)
    ints_list = Property(list[int], type=PropertyType.intVector, id=15, uid=1015)
    longs_list = Property(list[int], type=PropertyType.longVector, id=16, uid=1016)
    floats_list = Property(list[float], type=PropertyType.floatVector, id=17, uid=1017)
    doubles_list = Property(list[float], type=PropertyType.doubleVector, id=18, uid=1018)
    transient = ""  # not "Property" so it's not stored

    def __init__(self, string: str = ""):
        self.str = string
