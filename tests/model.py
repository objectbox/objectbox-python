from objectbox.model import *
from datetime import datetime


@Entity()
class TestEntity:
    id = Id()
    # TODO Enable indexing dynamically, e.g. have a constructor to enable index(es).
    #      E.g. indexString=False (defaults to false). Same for bytes.
    # TODO Test HASH and HASH64 indices (only supported for strings)
    str = String(index=Index())
    bool = Bool()
    int64 = Int64(index=Index())
    int32 = Int32()
    int16 = Int16()
    int8 = Int8()
    float64 = Float64()
    float32 = Float32()
    bools = BoolVector()
    bytes = Int8Vector()
    shorts = Int16Vector()
    chars = CharVector()
    ints = Int32Vector()
    longs = Int64Vector()
    floats = Float32Vector()
    doubles = Float64Vector()
    bools_list = BoolList()
    shorts_list = Int16List()
    chars_list = CharList()
    ints_list = Int32List()
    longs_list = Int64List()
    floats_list = Float32List()
    doubles_list = Float64List()
    date = Date()
    date_nano = DateNano(int)
    flex = Flex()
    bytes = Bytes()
    transient = ""  # not "Property" so it's not stored


@Entity()
class TestEntityDatetime:
    id = Id()
    date = Date(float)
    date_nano = DateNano()


@Entity()
class TestEntityFlex:
    id = Id()
    flex = Flex()


@Entity()
class VectorEntity:
    id = Id()
    name = String()
    vector_euclidean = Float32Vector(
        index=HnswIndex(
            dimensions=2, distance_type=VectorDistanceType.EUCLIDEAN
        ),
    )
    vector_cosine = Float32Vector(
        index=HnswIndex(
            dimensions=2, distance_type=VectorDistanceType.COSINE
        ),
    )
    vector_dot_product = Float32Vector(
        index=HnswIndex(
            dimensions=2, distance_type=VectorDistanceType.DOT_PRODUCT
        ),
    )
    # TODO: dot-product non-normalized 
    #vector_dot_product_non_normalized = Float32Vector(
    #    id=6,
    #    uid=4006,
    #    index=HnswIndex(
    #        id=6,
    #        uid=40004,
    #        dimensions=2,
    #        distance_type=VectorDistanceType.DOT_PRODUCT_NON_NORMALIZED,
    #    ),
    #)
