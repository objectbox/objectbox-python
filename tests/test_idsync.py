import json
import pytest
import os
from numpy.testing import assert_approx_equal
from objectbox import *
from objectbox.model import *
from objectbox.model.entity import _Entity
from objectbox.model.idsync import sync_model
from objectbox.c import CoreException
from os import path

from tests.common import remove_json_model_file


class _TestEnv:
    """
    Test setup/tear-down of model json files, db store and utils.
    Starts "fresh" on construction: deletes the model json file and the db files.
    """
    def __init__(self):
        self.model_path = 'test.json'
        if path.exists(self.model_path):
            os.remove(self.model_path)
        self._model = None
        self.db_path = 'testdb'
        Store.remove_db_files(self.db_path)
        self._store = None  # Last created store

    def sync(self, model: Model) -> bool:
        """ Returns True if changes were made and the model JSON was written. """
        self._model = model
        return sync_model(self._model, self.model_path)

    def json(self):
        return json.load(open(self.model_path))

    def create_store(self):
        assert self._model is not None, "Model must be set before creating store"
        if self._store is not None:
            self._store.close()
        self._store = Store(model=self._model, directory=self.db_path)
        return self._store

    def close(self):
        if self._store is not None:
            self._store.close()


def reset_ids(entity: _Entity):
    entity._iduid = IdUid(0, 0)
    entity._last_property_iduid = IdUid(0, 0)
    for prop in entity._properties:
        prop.iduid = IdUid(0, 0)
        if prop.index:
            prop.index.iduid = IdUid(0, 0)

@pytest.fixture
def env():
    env_ = _TestEnv()
    yield env_
    env_.close()


def test_empty_model(env):
    """ Tests situations where the user attempts to sync an empty model. """

    # JSON file didn't exist, user syncs an empty model -> no JSON file is generated
    model = Model()
    with pytest.raises(ValueError):
        assert not env.sync(model)
    assert not path.exists(env.model_path)

    # Init the JSON file with an entity
    @Entity()
    class MyEntity:
        id = Id()
    model = Model()
    model.entity(MyEntity)
    assert env.sync(model)  # Model JSON written

    # JSON file exists, user tries to sync an empty model: must fail with JSON file untouched
    model = Model()
    with pytest.raises(ValueError):
       env.sync(model)

    doc = env.json()
    assert len(doc['entities']) == 1
    assert doc['entities'][0]['id'] == str(MyEntity._iduid)


def test_json(env):
    @Entity()
    class MyEntity:
        id = Id()
        my_string = String()
        my_string_indexed = String(index=Index())

    model = Model()
    model.entity(MyEntity)
    env.sync(model)
    doc = env.json()
    # debug: pprint(doc)

    json_e0 = doc['entities'][0]
    e0_id = json_e0['id']
    assert e0_id == str(MyEntity._iduid)
    assert e0_id.startswith("1:")
    assert json_e0['name'] == "MyEntity"

    json_p0 = json_e0['properties'][0]
    p0_id = json_p0['id']
    assert p0_id == str(MyEntity._get_property('id').iduid)
    assert p0_id.startswith("1:")
    assert json_p0['name'] == "id"
    assert json_p0['flags'] == 1
    assert json_p0.get('indexId') is None

    json_p1 = json_e0['properties'][1]
    assert json_p1['id'] == str(MyEntity._get_property('my_string').iduid)
    assert json_p1['name'] == "my_string"
    assert json_p1.get('flags') is None
    assert json_p1.get('indexId') is None

    json_p2 = json_e0['properties'][2]
    assert json_p2['id'] == str(MyEntity._get_property('my_string_indexed').iduid)
    assert json_p2['name'] == "my_string_indexed"
    assert json_p2['flags'] == 8
    assert json_p2['indexId'] == str(MyEntity._get_property('my_string_indexed').index.iduid)
    assert json_e0['lastPropertyId'] == json_p2['id']

    assert doc['lastEntityId'] == e0_id
    assert doc['lastIndexId'] == json_p2['indexId']


def test_basics(env):
    @Entity()
    class MyEntity:
        id = Id()
        name = String()

    model = Model()
    model.entity(MyEntity)
    env.sync(model)
    assert MyEntity._id == 1
    assert MyEntity._uid != 0
    entity_ids = str(MyEntity._iduid)

    # create new database and populate with two objects
    store = env.create_store()
    entityBox = store.box(MyEntity)
    entityBox.put(MyEntity(name="foo"),MyEntity(name="bar"))
    assert entityBox.count() == 2
    del entityBox

    # recreate model using existing model json and open existing database 
    model = Model()
    @Entity()
    class MyEntity:
        id = Id()
        name = String()
    model.entity(MyEntity)
    assert str(model.entities[0]._iduid) == "0:0"
    env.sync(model)
    assert str(model.entities[0]._iduid) == entity_ids

    # open existing database 
    store = env.create_store()
    entityBox = store.box(MyEntity)
    assert entityBox.count() == 2

def test_entity_add(env):
    @Entity()
    class MyEntity1:
        id = Id()
        name = String()
    model = Model()
    model.entity(MyEntity1)
    env.sync(model)
    e0_iduid = IdUid(MyEntity1._id, MyEntity1._uid)
    store = env.create_store()
    box = store.box(MyEntity1)
    box.put( MyEntity1(name="foo"), MyEntity1(name="bar"))
    assert box.count() == 2

    @Entity()
    class MyEntity2:
        id = Id()
        name = String()
        value = Int64()
    model = Model()
    reset_ids(MyEntity1)
    model.entity(MyEntity1)
    model.entity(MyEntity2)
    assert str(model.entities[0]._iduid) == "0:0"
    env.sync(model)
    assert model.entities[0]._iduid == e0_iduid
    store = env.create_store()
    box1 = store.box(MyEntity1)
    assert box1.count() == 2
    box2 = store.box(MyEntity2)
    box2.put( MyEntity2(name="foo"), MyEntity2(name="bar"))
    assert box2.count() == 2

def test_entity_remove(env):
    @Entity()
    class MyEntity1:
        id = Id()
        name = String()
    @Entity()
    class MyEntity2:
        id = Id()
        name = String()
        value = Int64()
    model = Model()
    model.entity(MyEntity1)
    model.entity(MyEntity2)
    env.sync(model)
    store = env.create_store()
    box1 = store.box(MyEntity1)
    box1.put( MyEntity1(name="foo"), MyEntity1(name="bar"))
    box2 = store.box(MyEntity2)
    box2.put( MyEntity2(name="foo"), MyEntity2(name="bar"))
    assert box1.count() == 2
    assert box2.count() == 2

    # Re-create a model without MyEntity2 

    model = Model()
    reset_ids(MyEntity1)
    model.entity(MyEntity1)
    env.sync(model)
    store = env.create_store()
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
        name = String()
    model.entity(MyEntity)
    env.sync(model)

    # Save uid of entity for renaming purposes..
    uid = MyEntity._uid # iduid.uid
    assert uid != 0
    # Debug: print("UID: "+ str(uid))

    store = env.create_store()
    box = store.box(MyEntity)
    box.put(MyEntity(name="foo"),MyEntity(name="bar"))
    assert box.count() == 2
    del box

    @Entity(uid=uid)
    class MyRenamedEntity:
        id = Id()
        name = String()

    model = Model()
    model.entity(MyRenamedEntity)
    env.sync(model)
    store = env.create_store()
    box = store.box(MyRenamedEntity)
    assert box.count() == 2


def test_entity_rename_2(env):
    # Init JSON file
    @Entity(uid=365)
    class Entity1:
        id = Id()

    @Entity(uid=324)
    class Entity2:
        id = Id()

    @Entity(uid=890)
    class Entity3:
        id = Id()

    model = Model()
    model.entity(Entity1)
    model.entity(Entity2)
    model.entity(Entity3)
    assert env.sync(model)
    assert model.last_entity_iduid == IdUid(3, 890)

    # Rename Entity2 -> Entity4 (same UID)
    @Entity(uid=324)
    class Entity4:
        id = Id()
        name = String()  # Add one property also

    model = Model()
    reset_ids(Entity1)
    reset_ids(Entity3)
    model.entity(Entity1)
    model.entity(Entity3)
    model.entity(Entity4)
    assert env.sync(model)
    assert Entity4._iduid == IdUid(2, 324)  # Same ID/UID of Entity2 (renaming)
    assert model.last_entity_iduid == IdUid(3, 890)


def test_prop_add(env):

    @Entity()
    class MyEntity:
        id = Id()
        name = String()
    model = Model()
    model.entity(MyEntity)
    env.sync(model)
    store = env.create_store()
    box = store.box(MyEntity)
    box.put( MyEntity(name="foo"), MyEntity(name="bar"))
    del box

    @Entity()
    class MyEntity:
        id = Id()
        name = String()
        value = Property(int, type=PropertyType.int)

    model = Model()
    model.entity(MyEntity)
    env.sync(model)
    store = env.create_store()
    box = store.box(MyEntity)

    assert box.count() == 2

def test_prop_remove(env):

    @Entity()
    class MyEntity:
        id = Id()
        name = String()
        value = Property(int, type=PropertyType.int)

    model = Model()
    model.entity(MyEntity)
    env.sync(model)
    store = env.create_store()
    box = store.box(MyEntity)
    box.put( MyEntity(name="foo"), MyEntity(name="bar"))
    del box

    @Entity()
    class MyEntity:
        id = Id()
        name = String()

    model = Model()
    model.entity(MyEntity)
    env.sync(model)
    store = env.create_store()
    box = store.box(MyEntity)
    assert box.count() == 2


def test_prop_rename(env):
    @Entity()
    class EntityA:
        id = Id()
        name = String()

    model = Model()
    model.entity(EntityA)
    env.sync(model)
    store = env.create_store()
    box = store.box(EntityA)
    box.put(EntityA(name="Luca"))
    assert box.count() == 1
    assert box.get(1).name == "Luca"
    assert not hasattr(box.get(1), "renamed_name")

    entity1_iduid = EntityA._iduid
    name = EntityA._get_property("name")
    name_iduid = name.iduid
    print(f"Entity.name ID/UID: {name.iduid}")

    del box  # Close store

    # *** Rename ***

    @Entity()
    class EntityA:
        id = Id()
        renamed_name = Property(str, uid=name.uid)  # Renamed property (same UID as "name")

    model = Model()
    model.entity(EntityA)
    env.sync(model)
    store = env.create_store()

    # Check ID/UID(s) are preserved after renaming
    entity2_iduid = EntityA._iduid
    renamed_name = EntityA._get_property("renamed_name")
    renamed_name_iduid = renamed_name.iduid
    print(f"Entity.renamed_name ID/UID: {renamed_name_iduid}")
    assert entity1_iduid == entity2_iduid
    assert name_iduid == renamed_name_iduid

    # Check property value is preserved after renaming
    box = store.box(EntityA)
    assert box.count() == 1
    assert not hasattr(box.get(1), "name")
    assert box.get(1).renamed_name == "Luca"


def test_model_json_updates(env):
    """ Tests situations where the model JSON should be written/should not be written. """

    def sync_entities(*entities: _Entity):
        model = Model()
        for entity in entities:
            model.entity(entity)
        return env.sync(model)

    # Init
    @Entity()
    class EntityA:
        id = Id()
        name = String()
    assert sync_entities(EntityA)

    # Add entity
    @Entity()
    class EntityB:
        id = Id()
        name = String()
    assert sync_entities(EntityB)

    entityb_uid = EntityB._uid

    # Rename entity
    @Entity(uid=entityb_uid)
    class EntityC:
        id = Id()
        name = String()
    assert sync_entities(EntityC)

    # Noop
    model = Model()
    model.entity(EntityC)
    assert not env.sync(model)

    # Add entity
    @Entity()
    class EntityD:
        id = Id()
        name = String()
        age = Int8()
    assert sync_entities(EntityC, EntityD)

    # Noop
    assert sync_entities(EntityC, EntityD) is False

    # Replace entity
    @Entity()
    class EntityE:
        id = Id()
    assert sync_entities(EntityD, EntityE)

    # Noop
    assert sync_entities(EntityD, EntityE) is False

    # Remove entity
    assert sync_entities(EntityD)

    # Noop
    assert sync_entities(EntityD) is False

    # Add property
    @Entity()
    class EntityD:
        id = Id()
        name = String()
        age = Int8()
        my_prop = String()
    assert sync_entities(EntityD)

    my_prop_uid = EntityD._get_property("my_prop").uid

    # Rename property
    @Entity()
    class EntityD:
        id = Id()
        name = String()
        age = Int8()
        my_prop_renamed = String(uid=my_prop_uid)
    assert sync_entities(EntityD)

    # Noop
    assert sync_entities(EntityD) is False

    # Remove property
    @Entity()
    class EntityD:
        id = Id()
        name = String()
        age = Int8()
    assert sync_entities(EntityD)


def test_model_uid_already_assigned(env):
    """ Tests an invalid situation where the user supplies a UID which is already present elsewhere in the JSON. """

    @Entity()
    class EntityA:
        id = Id()
        prop = Property(str)

    model = Model()
    model.entity(EntityA)
    env.sync(model)

    entitya_uid = EntityA._uid

    # Rename property, but use a UID which is already assigned
    @Entity()
    class EntityA:
        id = Id()
        renamed_prop = Property(str, uid=entitya_uid)

    model = Model()
    model.entity(EntityA)
    with pytest.raises(ValueError) as e:
        env.sync(model)
    assert f"User supplied UID {entitya_uid} is already assigned elsewhere" == str(e.value)


def test_models_named(env):
    @Entity(model="modelA")
    class EntityA:
        id = Id
        text_a = String

    @Entity(model="modelB")
    class EntityB:
        id = Id
        int_b = Int64

    @Entity(model="modelB")
    class EntityB2:
        id = Id()
        float_b = Float64

    Store.remove_db_files("test-db-model-a")
    Store.remove_db_files("test-db-model-b")
    remove_json_model_file()
    store_a = Store(model="modelA", directory="test-db-model-a")
    remove_json_model_file()
    store_b = Store(model="modelB", directory="test-db-model-b")

    box_a = store_a.box(EntityA)
    id = box_a.put(EntityA(text_a="ah"))
    assert id != 0
    assert box_a.get(id).text_a == "ah"

    # TODO to make this work we Store/Box to check if the type is actually registered.
    #      This might require to store the (Python) model in the Store.
    # with pytest.raises(ValueError):
    #     store_a.box(EntityB)

    with pytest.raises(CoreException):
        store_a.box(EntityB2)

    box_b = store_b.box(EntityB)
    id = box_b.put(EntityB(int_b=42))
    assert id != 0
    assert box_b.get(id).int_b == 42

    box_b2 = store_b.box(EntityB2)
    id = box_b2.put(EntityB2(float_b=3.141))
    assert id != 0
    assert_approx_equal(box_b2.get(id).float_b, 3.141)

    # TODO to make this work we Store/Box to check if the type is actually registered.
    #      This might require to store the (Python) model in the Store.
    # with pytest.raises(ValueError):
    #     store_b.box(EntityA)
