from objectbox.model import *


@Entity(id=1, uid=1)
class TaskInfo:
    id = Id(id=1, uid=1001)
    text = Property(str, id=2, uid=1002)

@Entity(id=2, uid=2)
class Task:
    id = Id(id=1, uid=1001)
    info = Property(TaskInfo, type=PropertyType.relation, target_id=IdUid(1, 1), id=2, uid=1002)

    # TODO property type DATE
    date_created = Property(int, id=3, uid=1003)
    date_finished = Property(int, id=4, uid=1004)

def get_objectbox_model():
    m = Model()
    m.entity(TaskInfo, last_property_id=IdUid(2, 1002))
    m.entity(Task, last_property_id=IdUid(4, 1004))
    m.last_entity_id = IdUid(2, 2)
    m.last_relation_id = IdUid(1, 1)
    return m
