from objectbox.model import *


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
    transient = ""  # not "Property" so it's not stored

    def __init__(self, string: str = ""):
        self.str = string
