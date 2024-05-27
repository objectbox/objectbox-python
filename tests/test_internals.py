from objectbox import *
from objectbox.model import *
from objectbox.model.idsync import sync_model

import os
import os.path
import pytest

class _TestEnv:
    """
    Test setup/tear-down of model json files, db store and utils.
    Starts "fresh" on construction: deletes the model json file and the db files.
    """
    def __init__(self):
        self.model_path = 'test.json'
        if os.path.exists(self.model_path):
            os.remove(self.model_path)
        self.model = None
        self.db_path = 'testdb'
        Store.remove_db_files(self.db_path)

    def sync(self, model: Model) -> bool:
        """ Returns True if changes were made and the model JSON was written. """
        self.model = model
        return sync_model(self.model, self.model_path)

    def store(self):
        assert self.model is not None
        return Store(model=self.model, directory=self.db_path)

@pytest.fixture
def env():
    return _TestEnv()


def test_property_name_clash(env):
    @Entity()
    class MyEntity:
        id = Id()
        user_type = String()
        iduid = String()
        name = String()
        last_property_id = String()
        properties = String()
        offset_properties = String()
        id_property = String()
        _id = String() # a bad one; this one don't work directly
        a_safe_one = String()

    model = Model()
    model.entity(MyEntity)
    env.sync(model)  
    store = env.store()

    box = store.box(MyEntity)
    id1 = box.put(
        MyEntity(
            user_type="foobar",
            iduid="123",
            name="bar",
            last_property_id="blub",
            properties="baz",
            offset_properties="blah",
            id_property = "kazong",
            _id="fooz",
            a_safe_one="blah",
        )
    )
    assert box.count() == 1

    assert len(box.query(MyEntity.id.equals(id1)).build().find()) == 1
    assert len(box.query(MyEntity.iduid.equals("123")).build().find()) == 1
    assert len(box.query(MyEntity.user_type.equals("foobar")).build().find()) == 1
    assert len(box.query(MyEntity.name.equals("bar")).build().find()) == 1
    assert len(box.query(MyEntity.last_property_id.equals("blub")).build().find()) == 1
    assert len(box.query(MyEntity.properties.equals("baz")).build().find()) == 1
    assert len(box.query(MyEntity.offset_properties.equals("blah")).build().find()) == 1
    assert len(box.query(MyEntity.id_property.equals("kazong")).build().find()) == 1
    with pytest.raises(AttributeError):
        MyEntity._id.equals("fooz")
    assert len(box.query(MyEntity._get_property("_id").equals("fooz")).build().find()) == 1
    assert len(box.query(MyEntity.a_safe_one.equals("blah")).build().find()) == 1


def test_entity_attribute_methods_nameclash_check():
    # Test ensures we do not leave occasional instance attributes or class methods/attributes in
    # helper class _Entity which might collide with user-defined property names.
    # (We expect users not use use underscore to guarantee convient access to properties as-is via '.' operator)

    # To check instance as well as class data, we create a dummy entity which we'll scan next.
    @Entity()
    class MyEntity:
        id = Id()
    
    not_prefixed = []

    for attrname in MyEntity.__dict__:
        if not attrname.startswith("_"):
            not_prefixed.append(attrname)

    for methodname in MyEntity.__class__.__dict__:
        if not methodname.startswith("_"):
            not_prefixed.append(methodname)

    assert (
            len(not_prefixed) == 0
    ), f"INTERNAL: Public attributes/methods(s) detected in Class _Entity: {not_prefixed}\nPlease prefix with '_' to prevent name-collision with Property field-names."
