from objectbox import *
from objectbox.model import *
from objectbox.model.idsync import sync_model
from objectbox.c import CoreException
import json
from pprint import pprint
import os
import tests.model
import pytest

class _TestEnv:
    """Test setup/tear-down of model json files, db store and utils."""
    def __init__(self):
        self.model_path = 'test.json'
        if os.path.exists(self.model_path):
            os.remove(self.model_path)
        self.db_path = 'testdb'
        Store.remove_db_files(self.db_path)
    def sync(self, model):
        self.model = model
        sync_model(self.model, self.model_path)
    def json(self):
        return json.load(open(self.model_path))
    def store(self):
        return Store(model=self.model, directory=self.db_path)
        
@pytest.fixture
def env():
    return _TestEnv()

def test_empty(env):
    model = Model()
    env.sync(model)
    doc = env.json()
    assert doc['_note1']
    assert doc['_note2']
    assert doc['_note3']
    assert len(doc['entities']) == 0
    assert doc['lastEntityId'] == '0:0'
    assert doc['lastIndexId'] == '0:0' # NOTE: objectbox-generator outputs ""
    assert doc['modelVersionParserMinimum'] >= 5
    # debug: pprint(doc)
    #
    # TODO: sync with objectbox-generator empty fbs
    # assert doc['modelVersion'] == 5 
    # assert doc['lastIndex'] == ""
    # assert doc['lastRelationId'] == ""
    # assert len(doc['retiredEntityUids']) == 0
    # assert len(doc['retiredIndexUids']) == 0
    # assert len(doc['retiredPropertyUids']) == 0
    # assert len(doc['retiredRelationUids']) == 0
    # assert len(doc['version']) == 1

def test_basics(env):
    @Entity()
    class MyEntity:
        id = Id()
        name = Property(str)
    model = Model()
    model.entity(MyEntity)
    env.sync(model)
    doc = env.json() 
    # debug: pprint(doc) 
    e0 = doc['entities'][0] 
    assert e0['id'] == str(MyEntity.iduid)
    assert e0['name'] == "MyEntity"
    props = e0['properties'] 
    assert props[0]['id'] == str(MyEntity.get_property('id').iduid)
   
    # create new database and populate with two objects
    store = env.store()
    entityBox = store.box(MyEntity)
    entityBox.put(MyEntity(name="foo"),MyEntity(name="bar"))
    assert entityBox.count() == 2
    del entityBox
    store.close()
    del store
   
    # recreate model using existing model json and open existing database 
    model = Model()
    @Entity()
    class MyEntity:
        id = Id()
        name = Property(str)
    model.entity(MyEntity)
    env.sync(model)
   
    # open existing database 
    store = env.store()
    entityBox = store.box(MyEntity)
    assert entityBox.count() == 2

def test_entity_add(env):
    @Entity()
    class MyEntity1:
        id = Id()
        name = Property(str)
    model = Model()
    model.entity(MyEntity1)
    env.sync(model)
    store = env.store()
    box = store.box(MyEntity1)
    box.put( MyEntity1(name="foo"), MyEntity1(name="bar"))
    assert box.count() == 2
    store.close()
    del store
    
    @Entity()
    class MyEntity2:
        id = Id()
        name = Property(str)
        value = Property(int)
    model = Model()
    model.entity(MyEntity1)
    model.entity(MyEntity2)
    env.sync(model)
    store = env.store()
    box1 = store.box(MyEntity1)
    assert box1.count() == 2
    box2 = store.box(MyEntity2)
    box2.put( MyEntity2(name="foo"), MyEntity2(name="bar"))
    assert box2.count() == 2     

def test_entity_remove(env):
    @Entity()
    class MyEntity1:
        id = Id()
        name = Property(str)
    @Entity()
    class MyEntity2:
        id = Id()
        name = Property(str)
        value = Property(int)
    model = Model()
    model.entity(MyEntity1)
    model.entity(MyEntity2)
    env.sync(model)
    store = env.store()
    box1 = store.box(MyEntity1)
    box1.put( MyEntity1(name="foo"), MyEntity1(name="bar"))
    box2 = store.box(MyEntity2)
    box2.put( MyEntity2(name="foo"), MyEntity2(name="bar"))
    assert box1.count() == 2
    assert box2.count() == 2

    store.close()
    del store
   
    # Re-create a model without MyEntity2 
    
    model = Model()
    model.entity(MyEntity1)
    env.sync(model)
    store = env.store()
    box1 = store.box(MyEntity1)
    assert box1.count() == 2

    # MyEntity2 is gone and should raise CoreException
    with pytest.raises(CoreException): 
        box2 = store.box(MyEntity2)
    
def test_entity_rename(env):
    model = Model()
    @Entity()
    class MyEntity:
        id = Id()
        name = Property(str)
    model.entity(MyEntity)
    env.sync(model)
    
    # Save uid of entity for renaming purposes..
    uid = MyEntity.uid # iduid.uid
    # Debug: print("UID: "+ str(uid))
 
    store = env.store()
    box = store.box(MyEntity)
    box.put(MyEntity(name="foo"),MyEntity(name="bar"))
    assert box.count() == 2
    del box
    store.close()
    del store
    
    @Entity(uid=uid)
    class MyRenamedEntity:
        id = Id()
        name = Property(str)

    model = Model()
    model.entity(MyRenamedEntity)
    env.sync(model)
    store = env.store()
    box = store.box(MyRenamedEntity)
    assert box.count() == 2


def test_prop_add(env):
    
    @Entity()
    class MyEntity:
        id = Id()
        name = Property(str)
    model = Model()
    model.entity(MyEntity)
    env.sync(model)
    store = env.store()
    box = store.box(MyEntity)
    box.put( MyEntity(name="foo"), MyEntity(name="bar"))
    del box
    store.close()
    del store

    @Entity()
    class MyEntity:
        id = Id()
        name = Property(str)
        value = Property(int, type=PropertyType.int)

    model = Model()
    model.entity(MyEntity)
    env.sync(model)
    store = env.store()
    box = store.box(MyEntity)

    assert box.count() == 2
  
def test_prop_remove(env):
    
    @Entity()
    class MyEntity:
        id = Id()
        name = Property(str)
        value = Property(int, type=PropertyType.int)

    model = Model()
    model.entity(MyEntity)
    env.sync(model)
    store = env.store()
    box = store.box(MyEntity)
    box.put( MyEntity(name="foo"), MyEntity(name="bar"))
    del box
    store.close()
    del store
    
    @Entity()
    class MyEntity:
        id = Id()
        name = Property(str)
    
    model = Model()
    model.entity(MyEntity)
    env.sync(model)
    store = env.store()
    box = store.box(MyEntity)
    assert box.count() == 2

# TODO: test_prop_rename ? Do we need a uid annotation for properties then?
