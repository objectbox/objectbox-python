from objectbox.model import *
from objectbox.model.properties import *
from objectbox.model.sync_model import sync_model
import objectbox
import numpy as np
import os.path

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
    sync_model(m, os.path.join(os.path.dirname(__file__),"obx-model.json") )
    return m
