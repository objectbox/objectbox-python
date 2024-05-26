from objectbox.model import *
from objectbox.model.properties import *
from objectbox.model.idsync import sync_model
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

