from objectbox.model import *
from objectbox.model.sync_model import sync_model

@Entity()
class Task:
    id = Id()
    text = String()

    date_created = Date(py_type=int)
    date_finished = Date(py_type=int)


def get_objectbox_model():
    m = Model()
    m.entity(Task)
    sync_model(m)
    return m
