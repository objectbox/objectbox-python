from objectbox.model import *


@Entity(id=1, uid=1)
class Task:
    id = Id(id=1, uid=1001)
    text = String(id=2, uid=1002)

    date_created = Date(py_type=int, id=3, uid=1003)
    date_finished = Date(py_type=int, id=4, uid=1004)


def get_objectbox_model():
    m = Model()
    m.entity(Task, last_property_id=IdUid(4, 1004))
    m.last_entity_id = IdUid(2, 2)
    return m
