from objectbox import *
from objectbox.model import *
import pytest

def test_property_name_clash():
    @Entity(id=1, uid=1)
    class MyEntity:
        id = Id(id=1, uid=5001)
        uid = String(id=2, uid=5002)
        cls = String(id=3, uid=5003)
        name = String(id=4, uid=5004)
        last_property_id = String(id=5, uid=5005)
        properties = String(id=6, uid=5006)
        _id = String(id=7, uid=5007) # a bad one; this one don't work directly
        a_safe_one = String(id=8, uid=5008)

    model = Model()
    model.entity(MyEntity, last_property_id=IdUid(8, 5008))
    model.last_entity_id = IdUid(1, 1)

    dbpath = "testdb"
    Store.remove_db_files(dbpath)
    store = Store(model=model, directory=dbpath)
    box = store.box(MyEntity)
    id1 = box.put(
        MyEntity(
            uid="123",
            cls="foo",
            name="bar",
            last_property_id="blub",
            properties="baz",
            _id="fooz",
            a_safe_one="blah",
        )
    )
    assert box.count() == 1

    assert len(box.query(MyEntity.id.equals(id1)).build().find()) == 1
    assert len(box.query(MyEntity.uid.equals("123")).build().find()) == 1
    assert len(box.query(MyEntity.cls.equals("foo")).build().find()) == 1
    assert len(box.query(MyEntity.name.equals("bar")).build().find()) == 1
    assert len(box.query(MyEntity.last_property_id.equals("blub")).build().find()) == 1
    assert len(box.query(MyEntity.properties.equals("baz")).build().find()) == 1
    with pytest.raises(AttributeError):
        MyEntity._id.equals("fooz")
    assert len(box.query(MyEntity._get_property("_id").equals("fooz")).build().find()) == 1
    assert len(box.query(MyEntity.a_safe_one.equals("blah")).build().find()) == 1


def test_entity_attribute_methods_nameclash_check():
    
    # Test ensures we do not leave occasional instance attributes or class methods/attributes in 
    # helper class _Entity which might collide with user-defined property names.
    # (We expect users not use use underscore to guarantee convient access to properties as-is via '.' operator) 
    
    # To check instance as well as class data, we create a dummy entity which we'll scan next.
    @Entity(id=1, uid=1)
    class MyEntity:
        id = Id(id=1, uid=5001)
    
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
