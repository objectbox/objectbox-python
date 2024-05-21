from objectbox.model import *
from objectbox.model.properties import *
from objectbox.model.sync_model import sync_model
import objectbox
import numpy as np


@Entity()
class City:
    id = Id()
    name = String()
    location = Float32Vector(index=HnswIndex(
        dimensions=2,
        distance_type=VectorDistanceType.EUCLIDEAN
    ))

def get_objectbox_model():
    m = Model()
    m.entity(City)
    sync_model(m)
    return m
