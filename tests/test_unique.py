import json

import pytest

from objectbox import *
from objectbox.c import (OBXPropertyFlags_INDEXED, OBXPropertyFlags_INDEX_HASH, OBXPropertyFlags_UNIQUE,
                         OBXPropertyFlags_UNIQUE_ON_CONFLICT_REPLACE)
from objectbox.exceptions import UniqueViolatedError


def _define():
    @Entity(model="unique")
    class User:
        id = Id
        email = String(unique=Unique())
        code = Int32(unique=Unique(ConflictStrategy.REPLACE))
        name = String

    return User


def _open(tmp_path, *entities) -> Store:
    model = Model()
    for entity in entities:
        model.entity(entity)
    return Store(model=model, directory=str(tmp_path / "db"), model_json_file=str(tmp_path / "model.json"))


def _json_flags(tmp_path):
    with open(str(tmp_path / "model.json")) as file:
        doc = json.load(file)
    return {p["name"]: p.get("flags", 0) for p in doc["entities"][0]["properties"]}


def test_unique_fail(tmp_path):
    User = _define()
    store = _open(tmp_path, User)
    box = store.box(User)
    ann = User(email="ann@example.com", code=1, name="Ann")
    box.put(ann)
    box.put(User(email="bob@example.com", code=2, name="Bob"))

    with pytest.raises(UniqueViolatedError, match="Unique constraint for User.email would be violated"):
        box.put(User(email="ann@example.com", code=3, name="Other Ann"))
    assert box.count() == 2

    # Updating the object having the value is fine
    ann.name = "Ann B."
    box.put(ann)
    assert box.get(ann.id).name == "Ann B."

    # put(list): nothing is put if one object violates the constraint (also within the list)
    with pytest.raises(UniqueViolatedError):
        box.put([User(email="cy@example.com", code=4), User(email="cy@example.com", code=5)])
    assert box.count() == 2
    store.close()

    flags = _json_flags(tmp_path)
    assert flags["email"] == OBXPropertyFlags_UNIQUE | OBXPropertyFlags_INDEXED | OBXPropertyFlags_INDEX_HASH
    assert flags["code"] == (OBXPropertyFlags_UNIQUE | OBXPropertyFlags_UNIQUE_ON_CONFLICT_REPLACE |
                             OBXPropertyFlags_INDEXED)
    assert flags["name"] == 0


def test_unique_replace(tmp_path):
    User = _define()
    store = _open(tmp_path, User)
    box = store.box(User)
    old_id = box.put(User(email="ann@example.com", code=1, name="Ann"))
    other_id = box.put(User(email="bob@example.com", code=2, name="Bob"))
    new_id = box.put(User(email="ann2@example.com", code=1, name="New Ann"))  # Replaces the object with code 1
    assert new_id != old_id
    assert box.get(old_id) is None
    assert [(o.id, o.name) for o in box.get_all()] == [(other_id, "Bob"), (new_id, "New Ann")]
    store.close()


def test_unique_args():
    # The class itself works like an instance (as for Index); unique implies an index (of the default type)
    prop = String(unique=Unique)
    assert isinstance(prop.unique, Unique) and prop.unique.on_conflict == ConflictStrategy.FAIL
    assert isinstance(prop.index, Index)
    assert prop._flags == OBXPropertyFlags_UNIQUE | OBXPropertyFlags_INDEXED | OBXPropertyFlags_INDEX_HASH

    # The index type can be given
    prop = String(unique=Unique(), index=Index(IndexType.VALUE))
    assert prop._flags == OBXPropertyFlags_UNIQUE | OBXPropertyFlags_INDEXED

    for invalid in (True, ConflictStrategy.REPLACE, "unique"):
        with pytest.raises(TypeError, match="unique must be a Unique"):
            String(unique=invalid)
    with pytest.raises(TypeError, match="A unique property can not have a HnswIndex"):
        Float32Vector(unique=Unique(), index=HnswIndex(dimensions=2))
    with pytest.raises(TypeError, match="Unexpected property argument.*: unique"):
        Id(unique=Unique())  # IDs are unique anyway


def test_unique_replace_only_one(tmp_path):
    @Entity(model="unique")
    class User:
        id = Id
        email = String(unique=Unique(ConflictStrategy.REPLACE))
        code = Int32(unique=Unique(ConflictStrategy.REPLACE))

    with pytest.raises(ValueError, match="Entity User: ConflictStrategy.REPLACE can only be used for one property, "
                                         "but is used for email, code"):
        _open(tmp_path, User)


def test_unique_sync_entity_requires_replace(tmp_path):
    @SyncEntity()
    @Entity(model="unique")
    class User:
        id = Id
        email = String(unique=Unique())

    with pytest.raises(ValueError, match=r"Sync entity User: unique properties must use "
                                         r"Unique\(ConflictStrategy.REPLACE\), but email do\(es\) not"):
        _open(tmp_path, User)

    @SyncEntity()
    @Entity(model="unique")
    class User:
        id = Id
        email = String(unique=Unique(ConflictStrategy.REPLACE))

    from objectbox.model.idsync import sync_model
    model = Model()
    model.entity(User)
    sync_model(model, str(tmp_path / "model.json"))  # Valid (opening needs the Sync library)
    assert _json_flags(tmp_path)["email"] & OBXPropertyFlags_UNIQUE_ON_CONFLICT_REPLACE


def test_unique_added(tmp_path):
    """ Unique can be added to an existing property (a flag change). """

    @Entity(model="unique")
    class User:
        id = Id
        email = String

    store = _open(tmp_path, User)
    store.box(User).put(User(email="ann@example.com"))
    store.close()

    @Entity(model="unique")
    class User:
        id = Id
        email = String(unique=Unique())

    store = _open(tmp_path, User)
    box = store.box(User)
    with pytest.raises(UniqueViolatedError):
        box.put(User(email="ann@example.com"))
    store.close()
