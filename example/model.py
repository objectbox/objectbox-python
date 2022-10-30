from datetime import datetime
from objectbox.model import *


@Entity(id=1, uid=1)
class Task:
    id = Id(id=1, uid=1001)
    text = Property(str, id=2, uid=1002)

    date_created = Property(datetime, type=PropertyType.dateNano, id=3, uid=1003)
    date_finished = Property(datetime, id=4, uid=1004)


def get_objectbox_model():
    m = Model()
    m.entity(Task, last_property_id=IdUid(4, 1004))
    m.last_entity_id = IdUid(1, 1)
    return m
