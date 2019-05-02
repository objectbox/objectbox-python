from objectbox.model import *


@Entity(id=1, uid=1)
class TestEntity:
    id = Id(id=1, uid=1001)
    str = Property(str, id=2, uid=1002)
    bool = Property(bool, id=3, uid=1003)
    int = Property(int, id=4, uid=1004)
    float = Property(float, id=5, uid=1005)
    bytes = Property(bytes, id=6, uid=1006)
    transient: str = ""  # not "Property" so it's not stored
