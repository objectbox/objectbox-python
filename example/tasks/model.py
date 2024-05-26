from objectbox.model import *
from objectbox.model.idsync import sync_model
import os.path

@Entity()
class Task:
    id = Id()
    text = String()

    date_created = Date(py_type=int)
    date_finished = Date(py_type=int)

