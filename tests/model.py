from objectbox.model import *
from datetime import datetime

@Entity(id=1, uid=1)
class TestEntity:
    id = Id(id=1, uid=1001)
    # TODO Enable indexing dynamically, e.g. have a constructor to enable index(es).
    #      E.g. indexString=False (defaults to false). Same for bytes.
    # TODO Test HASH and HASH64 indices (only supported for strings)
    str = String(id=2, uid=1002,index=Index(id=1, uid=10001)) 
    bool = Bool(id=3, uid=1003)
    int64 = Int64(id=4, uid=1004,index=Index(id=2, uid=10002))
    int32 = Int32(id=5, uid=1005)
    int16 = Int16(id=6, uid=1006)
    int8 = Int8(id=7, uid=1007)
    float64 = Float64(id=8, uid=1008)
    float32 = Float32(id=9, uid=1009)
    bools = BoolVector(id=10, uid=1010) 
    bytes = Int8Vector(id=11, uid=1011) 
    shorts = Int16Vector(id=12, uid=1012) 
    chars = CharVector(id=13, uid=1013)
    ints = Int32Vector(id=14, uid=1014)
    longs = Int64Vector(id=15, uid=1015)
    floats = Float32Vector(id=16, uid=1016) 
    doubles = Float64Vector(id=17, uid=1017) 
    bools_list = BoolList(id=18, uid=1018)
    shorts_list = Int16List(id=19, uid=1019)
    chars_list = CharList(id=20, uid=1020)
    ints_list = Int32List(id=21, uid=1021)
    longs_list = Int64List(id=22, uid=1022)
    floats_list = Float32List(id=23, uid=1023)
    doubles_list = Float64List(id=24, uid=1024)
    date = Date(id=25, uid=1025) 
    date_nano = DateNano(id=26, uid=1026)
    flex = Flex(id=27, uid=1027) 
    transient = ""  # not "Property" so it's not stored


@Entity(id=2, uid=2)
class TestEntityDatetime:
    id = Id(id=1, uid=2001)
    date = Property(datetime, type=PropertyType.date, id=2, uid=2002)
    date_nano = Property(datetime, type=PropertyType.dateNano, id=3, uid=2003)


@Entity(id=3, uid=3)
class TestEntityFlex:
    id = Id(id=1, uid=3001)
    flex = Flex(id=2, uid=3002) 


@Entity(id=4, uid=4)
class VectorEntity:
    id = Id(id=1, uid=4001)
    name = String(id=2, uid=4002) 
    vector_euclidean = Float32Vector(id=3, uid=4003,index=HnswIndex(id=3, uid=40001, dimensions=2, distance_type=VectorDistanceType.EUCLIDEAN))
    vector_cosine = Float32Vector(id=4, uid=4004, index=HnswIndex(id=4, uid=40002, dimensions=2, distance_type=VectorDistanceType.COSINE))
    vector_dot_product = Float32Vector(id=5, uid=4005, index=HnswIndex(id=5, uid=40003, dimensions=2, distance_type=VectorDistanceType.DOT_PRODUCT))
    # vector_dot_product_non_normalized = FloatVector(index=HnswIndex(dimensions=2, distance_type=VectorDistanceType.DOT_PRODUCT_NON_NORMALIZED)
