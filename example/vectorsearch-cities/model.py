from objectbox.model import *
from objectbox.model.properties import *
import objectbox
import numpy as np


@Entity(id=1, uid=1)
class City:
    id = Id(id=1, uid=1001)
    name = Property(str, id=2, uid=1002)
    location = Property(np.ndarray, type=PropertyType.floatVector, id=3, uid=1003, index=HnswIndex(
        id=3, uid=10001,
        dimensions=2,
        distance_type=HnswDistanceType.EUCLIDEAN
    ))

def get_objectbox_model():
    m = Model()
    m.entity(City, last_property_id=IdUid(3, 1003))
    m.last_entity_id = IdUid(1, 1)
    m.last_index_id = IdUid(3,10001)
    return m
