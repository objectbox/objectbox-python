from datetime import datetime
from objectbox.model import *


@Entity()
class Task:
    id = Id()
    text = Property(str)

    # TODO property type DATE
    date_created = Property(datetime)
    date_finished = Property(datetime)


def get_objectbox_model():
    m = Model()
    m.entity(Task, last_property_id=IdUid(4, 1004))
    m.last_entity_id = IdUid(1, 1)
    return m
