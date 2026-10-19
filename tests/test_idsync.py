import json
import pytest
import os
from numpy.testing import assert_approx_equal
from objectbox import *
from objectbox.model import *
from objectbox.model.properties import Property, PropertyType, IndexType
from objectbox.model.entity import _Entity
from objectbox.model.idsync import sync_model
from objectbox.model.iduid import IdUid
from objectbox.exceptions import DbError
from objectbox.c import OBXPropertyFlags_INDEXED, OBXPropertyFlags_INDEX_HASH
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
    assert json_p1['name'] == "myString"
    assert json_p1.get('flags') is None
    assert json_p1.get('indexId') is None

    json_p2 = json_e0['properties'][2]
    assert json_p2['id'] == str(MyEntity._get_property('my_string_indexed').iduid)
    assert json_p2['name'] == "myStringIndexed"
    assert json_p2['flags'] == 8
    assert json_p2['indexId'] == str(MyEntity._get_property('my_string_indexed').index.iduid)
    assert json_e0['lastPropertyId'] == json_p2['id']

    assert doc['lastEntityId'] == e0_id
    assert doc['lastIndexId'] == json_p2['indexId']
    assert doc['lastRelationId'] == "0:0"  # Unassigned, like Java
    assert doc['modelVersion'] == 5  # Required e.g. by objectbox-generator
    assert doc['version'] == 1
    for key in ("retiredEntityUids", "retiredIndexUids", "retiredPropertyUids", "retiredRelationUids"):
        assert doc[key] == []


def test_camel_case():
    from objectbox.model.entity import camel_case
    assert camel_case("id") == "id"
    assert camel_case("date_created") == "dateCreated"
    assert camel_case("vec_2d") == "vec2d"
    assert camel_case("a__b") == "aB"
    assert camel_case("_internal_value") == "_internalValue"
    assert camel_case("type_") == "type_"
    assert camel_case("dateCreated") == "dateCreated"


def test_names_camel_case(env):
    @Entity()
    class MyEntity:
        id = Id
        date_created = Date
        text = String

    model = Model()
    model.entity(MyEntity)
    env.sync(model)
    names = [prop_json["name"] for prop_json in env.json()["entities"][0]["properties"]]
    assert names == ["id", "dateCreated", "text"]
    assert MyEntity.date_created.name == "date_created"  # The Python API uses the attribute names

    @Entity(python_names=True)
    class MyEntity:
        id = Id
        date_created = Date
        text = String

    model = Model()
    model.entity(MyEntity)
    env.sync(model)
    names = [prop_json["name"] for prop_json in env.json()["entities"][0]["properties"]]
    assert names == ["id", "date_created", "text"]


def test_names_camel_case_collision():
    with pytest.raises(ValueError, match="both have the name \"dateCreated\" in the database"):
        @Entity()
        class MyEntity:
            id = Id
            date_created = Date
            dateCreated = Date

    @Entity(python_names=True)
    class MyEntity:
        id = Id
        date_created = Date
        dateCreated = Date


def test_names_camel_case_upgrade(env):
    """ Model JSON and database with names as written in Python (before 5.0, or python_names=True): the properties
    are renamed to camelCase, keeping their IDs, UIDs and data; and back with python_names=True. """

    def define(python_names: bool):
        @Entity(python_names=python_names)
        class MyEntity:
            id = Id
            date_created = Int64
            sort_key = String(index=Index())

        return MyEntity

    MyEntity = define(python_names=True)
    model = Model()
    model.entity(MyEntity)
    env.sync(model)
    json_before = env.json()
    props_before = json_before["entities"][0]["properties"]
    assert [prop_json["name"] for prop_json in props_before] == ["id", "date_created", "sort_key"]
    env.create_store().box(MyEntity).put(MyEntity(date_created=42, sort_key="a"))

    for python_names, names in [(False, ["id", "dateCreated", "sortKey"]),
                                (True, ["id", "date_created", "sort_key"])]:
        MyEntity = define(python_names=python_names)
        model = Model()
        model.entity(MyEntity)
        assert env.sync(model)  # Renamed
        doc = env.json()
        props = doc["entities"][0]["properties"]
        assert [prop_json["name"] for prop_json in props] == names
        assert [(p["id"], p.get("indexId")) for p in props] == [(p["id"], p.get("indexId")) for p in props_before]
        assert doc["entities"][0]["lastPropertyId"] == json_before["entities"][0]["lastPropertyId"]
        assert doc["lastIndexId"] == json_before["lastIndexId"]

        box = env.create_store().box(MyEntity)
        objects = box.get_all()
        assert len(objects) == 1
        assert objects[0].date_created == 42
        assert objects[0].sort_key == "a"
        assert box.query(MyEntity.sort_key.equals("a")).build().count() == 1


def test_names_camel_case_upgrade_uid(env):
    """ Like test_names_camel_case_upgrade, but the property has a user supplied UID (matched by UID, not by name). """

    @Entity(python_names=True)
    class MyEntity:
        id = Id
        date_created = Int64(uid=7001)

    model = Model()
    model.entity(MyEntity)
    env.sync(model)
    prop_json_before = env.json()["entities"][0]["properties"][1]
    assert prop_json_before["name"] == "date_created"

    @Entity()
    class MyEntity:
        id = Id
        date_created = Int64(uid=7001)

    model = Model()
    model.entity(MyEntity)
    assert env.sync(model)  # Renamed
    prop_json = env.json()["entities"][0]["properties"][1]
    assert prop_json["name"] == "dateCreated"
    assert prop_json["id"] == prop_json_before["id"]


def test_json_empty_last_ids(env):
    """ The C++ and Go generators write an empty string for unassigned IDs, e.g. "lastIndexId": "". """
    with open(env.model_path, "w") as f:
        json.dump({
            "entities": [{
                "id": "1:6645479796472661392",
                "lastPropertyId": "2:8804670454579230281",
                "name": "MyEntity",
                "properties": [
                    {"id": "1:9211738071025439652", "name": "id", "type": 6, "flags": 1},
                    {"id": "2:8804670454579230281", "name": "text", "type": 9}
                ],
                "relations": []
            }],
            "lastEntityId": "1:6645479796472661392",
            "lastIndexId": "",
            "lastRelationId": "",
            "modelVersion": 5,
            "modelVersionParserMinimum": 5,
            "retiredEntityUids": [],
            "retiredIndexUids": [],
            "retiredPropertyUids": [],
            "retiredRelationUids": [],
            "version": 1
        }, f)

    @Entity()
    class MyEntity:
        id = Id()
        text = String()
        text_indexed = String(index=Index())

    model = Model()
    model.entity(MyEntity)
    env.sync(model)

    # IDs and UIDs from the JSON are kept; the first index gets ID 1
    assert str(MyEntity._iduid) == "1:6645479796472661392"
    assert str(MyEntity._get_property('text').iduid) == "2:8804670454579230281"
    assert MyEntity._get_property('text_indexed').iduid.id == 3
    index_iduid = MyEntity._get_property('text_indexed').index.iduid
    assert index_iduid.id == 1
    doc = env.json()
    assert doc['lastIndexId'] == str(index_iduid)
    assert doc['lastRelationId'] == ""  # Unassigned: kept like the file had it (objectbox-generator rejects "0:0")
    assert doc['entities'][0]['relations'] == []
    env.create_store().box(MyEntity).put(MyEntity(text="a", text_indexed="b"))


def test_json_empty_unassigned_written(env):
    """ An unassigned "last" ID managed by Python is written as "" if the loaded JSON uses "" (Go, C++). """
    with open(env.model_path, "w") as f:
        json.dump({
            "entities": [{
                "id": "1:6645479796472661392",
                "lastPropertyId": "1:9211738071025439652",
                "name": "MyEntity",
                "properties": [{"id": "1:9211738071025439652", "name": "id", "type": 6, "flags": 1}],
                "relations": []
            }],
            "lastEntityId": "1:6645479796472661392",
            "lastIndexId": "",
            "lastRelationId": "",
            "modelVersion": 5,
            "modelVersionParserMinimum": 5,
            "retiredEntityUids": [],
            "retiredIndexUids": [],
            "retiredPropertyUids": [],
            "retiredRelationUids": [],
            "version": 1
        }, f)

    @Entity()
    class MyEntity:
        id = Id()
        text = String()

    model = Model()
    model.entity(MyEntity)
    assert env.sync(model)
    doc = env.json()
    assert doc['lastIndexId'] == ""
    assert doc['lastRelationId'] == ""


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

    # MyEntity2 is gone and should raise StorageException
    with pytest.raises(DbError):
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

    with pytest.raises(DbError):
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
    store_a.close()
    store_b.close()


def test_sync_dynamic_entities(env):
    def create_entity(entity_name: str, dimensions: int, distance_type: VectorDistanceType, uid=0):
        DynamicEntity = type(entity_name, (), {
            "id": Id(),
            "name": String(),
            "vector": Float32Vector(index=HnswIndex(dimensions=dimensions, distance_type=distance_type))
        })
        return Entity(uid=uid)(DynamicEntity)  # Apply @Entity decorator

    CosineVectorEntity = create_entity("CosineVectorEntity",
                                       dimensions=2,
                                       distance_type=VectorDistanceType.COSINE)
    EuclideanVectorEntity = create_entity("EuclideanVectorEntity",
                                          dimensions=2,
                                          distance_type=VectorDistanceType.EUCLIDEAN)
    DotProductEntity = create_entity("DotProductEntity",
                                     dimensions=2,
                                     distance_type=VectorDistanceType.DOT_PRODUCT_NON_NORMALIZED)
    model = Model()
    model.entity(CosineVectorEntity)
    model.entity(EuclideanVectorEntity)
    model.entity(DotProductEntity)
    assert env.sync(model)
    CosineVectorEntity_iduid = CosineVectorEntity._iduid

    store = env.create_store()
    cosine_box = store.box(CosineVectorEntity)
    cosine_box.put(CosineVectorEntity(name="CosineObj1", vector=[2, 1]))
    cosine_box.put(CosineVectorEntity(name="CosineObj2", vector=[-6, 0]))
    euclidean_box = store.box(EuclideanVectorEntity)
    euclidean_box.put(EuclideanVectorEntity(name="EuclideanObj1", vector=[5, 4]))
    euclidean_box.put(EuclideanVectorEntity(name="EuclideanObj2", vector=[2, -6]))
    dot_product_box = store.box(DotProductEntity)
    dot_product_box.put(DotProductEntity(name="DotProductObj1", vector=[10, 0]))
    assert cosine_box.get(1).name == "CosineObj1"
    assert cosine_box.get(2).name == "CosineObj2"
    assert euclidean_box.get(1).name == "EuclideanObj1"
    assert euclidean_box.get(2).name == "EuclideanObj2"
    assert dot_product_box.get(1).name == "DotProductObj1"

    del cosine_box
    del euclidean_box
    del dot_product_box
    del store

    # Rename CosineVectorEntity to MyCosineVectorEntity
    MyCosineVectorEntity = create_entity("MyCosineVectorEntity",
                                         dimensions=2,
                                         distance_type=VectorDistanceType.COSINE,
                                         uid=CosineVectorEntity_iduid.uid)
    model = Model()
    model.entity(MyCosineVectorEntity)
    model.entity(EuclideanVectorEntity)
    model.entity(DotProductEntity)
    assert env.sync(model)
    assert CosineVectorEntity_iduid == MyCosineVectorEntity._iduid

    # Check MyCosineVectorEntity objects are preserved after renaming
    store = env.create_store()
    cosine_box = store.box(MyCosineVectorEntity)
    assert cosine_box.get(1).name == "CosineObj1"
    assert cosine_box.get(2).name == "CosineObj2"


def _uid(iduid_str: str) -> int:
    return IdUid.from_str(iduid_str).uid


def test_retire_entity(env):
    """ Removing an entity retires its UID and those of its properties and indexes; "last" IDs are kept. """

    @Entity()
    class EntityA:
        id = Id()
        name = String()

    @Entity()
    class EntityB:
        id = Id()
        name = String(index=Index())

    model = Model()
    model.entity(EntityA)
    model.entity(EntityB)
    env.sync(model)
    doc_before = env.json()
    assert doc_before["retiredEntityUids"] == []
    assert doc_before["retiredPropertyUids"] == []
    assert doc_before["retiredIndexUids"] == []
    assert doc_before["retiredRelationUids"] == []
    b_uid = EntityB._uid
    b_prop_uids = [prop.uid for prop in EntityB._properties]
    b_index_uid = EntityB._get_property("name").index.uid
    env.create_store().box(EntityA).put(EntityA(name="a"))

    model = Model()
    reset_ids(EntityA)
    model.entity(EntityA)
    assert env.sync(model)
    doc = env.json()
    assert doc["retiredEntityUids"] == [b_uid]
    assert doc["retiredPropertyUids"] == b_prop_uids
    assert doc["retiredIndexUids"] == [b_index_uid]
    assert doc["retiredRelationUids"] == []
    assert doc["lastEntityId"] == doc_before["lastEntityId"]  # EntityB's, now a retired UID
    assert doc["lastIndexId"] == doc_before["lastIndexId"]
    assert env.create_store().box(EntityA).count() == 1

    # No changes: not written again, nothing retired twice
    model = Model()
    reset_ids(EntityA)
    model.entity(EntityA)
    assert not env.sync(model)
    assert env.json() == doc

    # A new entity gets a new ID (EntityB's is not used again)
    @Entity()
    class EntityC:
        id = Id()

    model = Model()
    reset_ids(EntityA)
    model.entity(EntityA)
    model.entity(EntityC)
    assert env.sync(model)
    assert EntityC._id == _uid_id(doc_before["lastEntityId"]) + 1
    assert EntityC._uid not in doc["retiredEntityUids"]
    assert env.json()["retiredEntityUids"] == [b_uid]


def _uid_id(iduid_str: str) -> int:
    return IdUid.from_str(iduid_str).id


def test_retire_property(env):
    """ Removing a property retires its UID and its index's; other properties and the data are kept. """

    @Entity()
    class MyEntity:
        id = Id()
        name = String()
        code = String(index=Index())
        value = Int64()

    model = Model()
    model.entity(MyEntity)
    env.sync(model)
    code = MyEntity._get_property("code")
    code_uid, code_index_uid = code.uid, code.index.uid
    value_uid = MyEntity._get_property("value").uid
    env.create_store().box(MyEntity).put(MyEntity(name="a", code="c", value=1))

    @Entity()
    class MyEntity:
        id = Id()
        name = String()
        value = Int64()

    model = Model()
    model.entity(MyEntity)
    assert env.sync(model)
    doc = env.json()
    assert doc["retiredPropertyUids"] == [code_uid]
    assert doc["retiredIndexUids"] == [code_index_uid]
    assert doc["retiredEntityUids"] == []
    assert MyEntity._get_property("value").uid == value_uid
    objects = env.create_store().box(MyEntity).get_all()
    assert [(o.name, o.value) for o in objects] == [("a", 1)]

    # Re-adding a property with the same name creates a new one (new UID), not the removed one
    @Entity()
    class MyEntity:
        id = Id()
        name = String()
        code = String(index=Index())
        value = Int64()

    model = Model()
    model.entity(MyEntity)
    assert env.sync(model)
    code = MyEntity._get_property("code")
    assert code.uid != code_uid
    assert code.index.uid != code_index_uid
    assert env.json()["retiredPropertyUids"] == [code_uid]
    assert env.create_store().box(MyEntity).get_all()[0].code == ""


def test_retire_index_uid_changed(env):
    """ A property whose index gets a different (user supplied) UID retires the previous index UID. """

    @Entity()
    class MyEntity:
        id = Id()
        name = String(index=Index())

    model = Model()
    model.entity(MyEntity)
    env.sync(model)
    old_index_uid = MyEntity._get_property("name").index.uid

    @Entity()
    class MyEntity:
        id = Id()
        name = String(index=Index(uid=1234567890123))

    model = Model()
    model.entity(MyEntity)
    assert env.sync(model)
    doc = env.json()
    assert doc["retiredIndexUids"] == [old_index_uid]
    assert doc["retiredPropertyUids"] == []
    assert doc["entities"][0]["properties"][1]["indexId"].endswith(":1234567890123")


def test_index_changes(env):
    """ Adding, changing and removing the index of an existing property keeps the property and its data; the JSON
    file gets the new flags and index ID, a removed index UID is retired. """

    def open_with(index):
        @Entity()
        class MyEntity:
            id = Id()
            name = String(index=index) if index else String()

        model = Model()
        model.entity(MyEntity)
        written = env.sync(model)
        store = env.create_store()
        box = store.box(MyEntity)
        if box.is_empty():
            box.put([MyEntity(name="n%d" % i) for i in range(100)])
        assert [o.name for o in box.query(MyEntity.name.equals("n42")).build().find()] == ["n42"]
        assert box.count() == 100
        prop_json = env.json()["entities"][0]["properties"][1]
        assert prop_json["id"] == "2:" + str(MyEntity._get_property("name").uid)  # Same property
        return written, prop_json

    written, prop_json = open_with(None)
    assert "indexId" not in prop_json and "flags" not in prop_json

    written, prop_json = open_with(Index())  # Added
    assert written
    assert prop_json["flags"] == OBXPropertyFlags_INDEXED
    index_id = prop_json["indexId"]
    assert index_id.startswith("1:")

    written, prop_json = open_with(Index(IndexType.HASH))  # Changed type: same index ID
    assert written
    assert prop_json["flags"] == OBXPropertyFlags_INDEXED | OBXPropertyFlags_INDEX_HASH
    assert prop_json["indexId"] == index_id

    written, prop_json = open_with(Index(IndexType.HASH))  # Unchanged
    assert not written

    written, prop_json = open_with(None)  # Removed
    assert written
    assert "indexId" not in prop_json and "flags" not in prop_json
    assert env.json()["retiredIndexUids"] == [_uid(index_id)]

    written, prop_json = open_with(Index())  # Added again: a new index ID
    assert written
    assert prop_json["indexId"].startswith("2:") and _uid(prop_json["indexId"]) != _uid(index_id)
    env.close()


def test_retire_not_on_rename(env):
    """ Renames (by UID, and the camelCase fallback for names stored before 5.0) retire nothing. """

    @Entity(python_names=True)
    class MyEntity:
        id = Id()
        date_created = Int64()
        title = String(index=Index())

    model = Model()
    model.entity(MyEntity)
    env.sync(model)
    entity_uid = MyEntity._uid
    title_uid = MyEntity._get_property("title").uid

    @Entity(uid=entity_uid)
    class MyRenamedEntity:
        id = Id()
        date_created = Int64()  # camelCase now: dateCreated
        headline = String(uid=title_uid, index=Index())

    model = Model()
    model.entity(MyRenamedEntity)
    assert env.sync(model)
    doc = env.json()
    for key in ("retiredEntityUids", "retiredPropertyUids", "retiredIndexUids", "retiredRelationUids"):
        assert doc[key] == [], key
    assert [p["name"] for p in doc["entities"][0]["properties"]] == ["id", "dateCreated", "headline"]


def test_retired_uid_not_reused(env):
    """ A user supplied UID of a removed property is rejected, for a property and for an entity. """

    @Entity()
    class MyEntity:
        id = Id()
        name = String()
        value = Int64()

    model = Model()
    model.entity(MyEntity)
    env.sync(model)
    value_uid = MyEntity._get_property("value").uid

    @Entity()
    class MyEntity:
        id = Id()
        name = String()

    model = Model()
    model.entity(MyEntity)
    assert env.sync(model)
    assert env.json()["retiredPropertyUids"] == [value_uid]

    @Entity()
    class MyEntity:
        id = Id()
        name = String()
        value = Int64(uid=value_uid)

    model = Model()
    model.entity(MyEntity)
    with pytest.raises(ValueError, match=f"User supplied UID {value_uid} was used by a removed entity, property or "
                                         f"index"):
        env.sync(model)

    @Entity(uid=value_uid)
    class OtherEntity:
        id = Id()

    model = Model()
    model.entity(OtherEntity)
    with pytest.raises(ValueError, match=f"User supplied UID {value_uid} was used by a removed"):
        env.sync(model)


# A model JSON file as written by another ObjectBox language (e.g. Java or Dart): with a standalone relation
# (e.g. a ToMany), retired UIDs and fields Python does not manage
_OTHER_LANGUAGE_JSON = {
    "_note1": "KEEP THIS FILE! Check it into a version control system (VCS) like git.",
    "entities": [
        {
            "id": "1:1001",
            "lastPropertyId": "3:1013",
            "name": "Student",
            "properties": [
                {"id": "1:1011", "name": "id", "type": 6, "flags": 1},
                {"id": "2:1012", "name": "name", "type": 9},
                {"id": "3:1013", "name": "teacherId", "type": 11, "flags": 520, "indexId": "1:1014",
                 "relationTarget": "Teacher"}
            ],
            "relations": [{"id": "1:1015", "name": "courses", "targetId": "3:1031"}]
        },
        {
            "id": "2:1002",
            "lastPropertyId": "2:1022",
            "name": "Teacher",
            "properties": [
                {"id": "1:1021", "name": "id", "type": 6, "flags": 1},
                {"id": "2:1022", "name": "name", "type": 9}
            ],
            "relations": []
        },
        {
            "id": "3:1031",
            "lastPropertyId": "2:1033",
            "name": "Course",
            "properties": [
                {"id": "1:1032", "name": "id", "type": 6, "flags": 1},
                {"id": "2:1033", "name": "title", "type": 9}
            ],
            "relations": [{"id": "2:1034", "name": "students", "targetId": "1:1001"}]
        }
    ],
    "lastEntityId": "4:1041",
    "lastIndexId": "2:1042",
    "lastRelationId": "2:1034",
    "lastSequenceId": "0:0",
    "modelVersion": 5,
    "modelVersionParserMinimum": 5,
    "retiredEntityUids": [1041],
    "retiredIndexUids": [1042],
    "retiredPropertyUids": [1043, 1044],
    "retiredRelationUids": [1045],
    "version": 1
}


def _other_language_entities(with_course: bool = True, extra_student_prop: bool = False):
    @Entity()
    class Teacher:
        id = Id()
        name = String()

    if extra_student_prop:
        @Entity()
        class Student:
            id = Id()
            name = String()
            teacher_id = Relation(Teacher)
            age = Int32()
    else:
        @Entity()
        class Student:
            id = Id()
            name = String()
            teacher_id = Relation(Teacher)

    @Entity()
    class Course:
        id = Id()
        title = String()

    return [Student, Teacher] + ([Course] if with_course else [])


def _write_other_language_json(env):
    with open(env.model_path, "w") as f:
        json.dump(_OTHER_LANGUAGE_JSON, f, indent=2)


def test_json_other_language_unchanged(env):
    """ A matching model leaves the JSON file of another ObjectBox language as it is (not written). """
    _write_other_language_json(env)
    with open(env.model_path) as f:
        before = f.read()
    model = Model()
    for entity in _other_language_entities():
        model.entity(entity)
    assert not env.sync(model)
    with open(env.model_path) as f:
        assert f.read() == before


def test_json_other_language_kept(env):
    """ When Python writes a JSON file of another ObjectBox language, it keeps what Python does not manage:
    standalone relations, retired UIDs and the other top-level fields. """
    _write_other_language_json(env)
    model = Model()
    for entity in _other_language_entities(extra_student_prop=True):
        model.entity(entity)
    assert env.sync(model)  # New property Student.age
    doc = env.json()

    other = _OTHER_LANGUAGE_JSON
    for key in ("lastEntityId", "lastIndexId", "lastRelationId", "lastSequenceId", "modelVersion", "version",
                "retiredEntityUids", "retiredIndexUids", "retiredPropertyUids", "retiredRelationUids"):
        assert doc[key] == other[key], key
    for entity_json, other_entity_json in zip(doc["entities"], other["entities"]):
        assert entity_json["id"] == other_entity_json["id"]
        assert entity_json["relations"] == other_entity_json["relations"]
    student_props = doc["entities"][0]["properties"]
    assert student_props[:3] == other["entities"][0]["properties"]  # Incl. relationTarget
    assert student_props[3]["name"] == "age"
    assert student_props[3]["id"].startswith("4:")
    assert doc["entities"][0]["lastPropertyId"] == student_props[3]["id"]


def test_json_other_language_generated_uids(env, monkeypatch):
    """ Generated UIDs skip retired UIDs and those of standalone relations. """
    _write_other_language_json(env)
    candidates = iter([1040, 1014, 1044, 4999])  # random.getrandbits(63) + 1: retired, relation, retired, free
    monkeypatch.setattr("objectbox.model.idsync.random.getrandbits", lambda bits: next(candidates))
    model = Model()
    for entity in _other_language_entities(extra_student_prop=True):
        model.entity(entity)
    assert env.sync(model)
    assert env.json()["entities"][0]["properties"][3]["id"] == "4:5000"


def test_json_other_language_entity_removed(env):
    """ Removing an entity with a standalone relation retires the relation, too; the relations of other entities
    (here one to the removed entity) are kept as they are. """
    _write_other_language_json(env)
    model = Model()
    for entity in _other_language_entities(with_course=False):
        model.entity(entity)
    assert env.sync(model)
    doc = env.json()
    assert doc["retiredEntityUids"] == [1041, 1031]
    assert doc["retiredPropertyUids"] == [1043, 1044, 1032, 1033]
    assert doc["retiredIndexUids"] == [1042]
    assert doc["retiredRelationUids"] == [1045, 1034]
    assert [e["name"] for e in doc["entities"]] == ["Student", "Teacher"]
    assert doc["entities"][0]["relations"] == _OTHER_LANGUAGE_JSON["entities"][0]["relations"]


def test_json_other_language_uids_reserved(env):
    """ UIDs of standalone relations and retired UIDs can not be supplied by the user for something else. """
    _write_other_language_json(env)
    for uid, message in ((1015, "is already assigned elsewhere"), (1045, "was used by a removed"),
                         (1041, "was used by a removed")):
        entities = _other_language_entities()

        @Entity(uid=uid)
        class Extra:
            id = Id()

        model = Model()
        for entity in entities + [Extra]:
            model.entity(entity)
        with pytest.raises(ValueError, match=f"User supplied UID {uid} {message}"):
            env.sync(model)
