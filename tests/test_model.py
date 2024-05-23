from objectbox.model import *
from objectbox import *
from objectbox.model.idsync import sync_model
import os
import os.path
    
def test_reuse_model():
    @Entity()
    class MyEntity:
        id = Id()
        name = String()

    model = Model()
    model.entity(MyEntity)
    model_filepath = "test-model.json"
    if os.path.exists(model_filepath):
        os.remove(model_filepath)
    sync_model(model, model_filepath)

    db1path = "test-db1"
    db2path = "test-db2"
    Store.remove_db_files(db1path)
    Store.remove_db_files(db2path)

    store1 = Store(model=model, directory=db1path)
    store2 = Store(model=model, directory=db2path)

    store1.close()
    store2.close()


def test_reuse_entity():
    @Entity()
    class MyEntity:
        id = Id()
        name = String()

    m1 = Model()
    m1.entity(MyEntity)
    model_filepath = "test-model1.json"
    if os.path.exists(model_filepath):
        os.remove(model_filepath)
    sync_model(m1, model_filepath)

    db1path = "test-db1"
    db2path = "test-db2"
    Store.remove_db_files(db1path)
    Store.remove_db_files(db2path)

    store1 = Store(model=m1, directory=db1path)

    box1 = store1.box(MyEntity)
    box1.put(MyEntity(name="foo"))
    assert box1.count() == 1

    m2 = Model()
    
    @Entity()
    class MyEntity2:
        id = Id()
        name = String()
        value = Int64()
    
    m2.entity(MyEntity2)
    m2.entity(MyEntity)
    model_filepath = "test-model2.json"
    if os.path.exists(model_filepath):
        os.remove(model_filepath)
    sync_model(m2, model_filepath)

    store2 = Store(model=m2, directory=db2path)
    box2 = store2.box(MyEntity)
    box2.put(MyEntity(name="bar"))
    box2.put(MyEntity(name="bar"))
    box2.put(MyEntity(name="bar"))
    assert box2.count() == 3

    box1.put(MyEntity(name="foo"))
    box1.put(MyEntity(name="foo"))
    assert box1.count() == 3
    
    store1.close()
    store2.close()
