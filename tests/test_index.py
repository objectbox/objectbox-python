import json

import pytest

from objectbox import *
from objectbox.c import (OBXPropertyFlags_INDEXED, OBXPropertyFlags_INDEX_HASH, OBXPropertyFlags_INDEX_HASH64,
                         OBXPropertyFlags_INDEX_PARTIAL_SKIP_ZERO)
from objectbox import IndexType  # Exported by the top-level module


def _define(name_index: Index):
    @Entity(model="index")
    class Item:
        id = Id
        name = String(index=name_index)
        number = Int64(index=Index())
        small = Int32(index=Index(IndexType.VALUE))

    return Item


def _open(tmp_path, entity) -> Store:
    model = Model()
    model.entity(entity)
    return Store(model=model, directory=str(tmp_path / "db"), model_json_file=str(tmp_path / "model.json"))


def _json_flags(tmp_path):
    with open(str(tmp_path / "model.json")) as file:
        doc = json.load(file)
    return {p["name"]: p.get("flags", 0) for p in doc["entities"][0]["properties"]}


@pytest.mark.parametrize("name_index, name_flags", [
    (Index(), OBXPropertyFlags_INDEXED | OBXPropertyFlags_INDEX_HASH),  # Default for String: hash
    (Index(IndexType.HASH), OBXPropertyFlags_INDEXED | OBXPropertyFlags_INDEX_HASH),
    (Index(IndexType.HASH64), OBXPropertyFlags_INDEXED | OBXPropertyFlags_INDEX_HASH64),
    (Index(IndexType.VALUE), OBXPropertyFlags_INDEXED),
])
def test_index_types(tmp_path, name_index, name_flags):
    Item = _define(name_index)
    store = _open(tmp_path, Item)
    box = store.box(Item)
    box.put([Item(name="n%d" % i, number=i, small=i) for i in range(100)])
    assert [o.number for o in box.query(Item.name.equals("n42")).build().find()] == [42]
    assert [o.name for o in box.query(Item.number.equals(7)).build().find()] == ["n7"]
    assert [o.name for o in box.query(Item.small.equals(8)).build().find()] == ["n8"]
    store.close()
    flags = _json_flags(tmp_path)
    assert flags["name"] == name_flags
    assert flags["number"] == OBXPropertyFlags_INDEXED  # Default for other types: value
    assert flags["small"] == OBXPropertyFlags_INDEXED


def test_index_default_changed(tmp_path):
    """ A String index created as a value index before 5.0 (the default then) becomes a hash index. """
    Item = _define(Index(IndexType.VALUE))
    store = _open(tmp_path, Item)
    store.box(Item).put([Item(name="n%d" % i, number=i) for i in range(100)])
    store.close()
    with open(str(tmp_path / "model.json")) as file:
        index_id = json.load(file)["entities"][0]["properties"][1]["indexId"]

    Item = _define(Index())
    store = _open(tmp_path, Item)
    box = store.box(Item)
    assert box.count() == 100
    assert [o.number for o in box.query(Item.name.equals("n42")).build().find()] == [42]
    box.put(Item(name="new"))
    assert box.query(Item.name.equals("new")).build().count() == 1
    store.close()
    assert _json_flags(tmp_path)["name"] == OBXPropertyFlags_INDEXED | OBXPropertyFlags_INDEX_HASH
    with open(str(tmp_path / "model.json")) as file:
        assert json.load(file)["entities"][0]["properties"][1]["indexId"] == index_id  # Same index


def test_relation_index_unchanged():
    @Entity(model="index")
    class Target:
        id = Id

    relation = Relation(Target)
    assert relation._flags == OBXPropertyFlags_INDEXED | OBXPropertyFlags_INDEX_PARTIAL_SKIP_ZERO


def test_index_class_as_arg(tmp_path):
    """ The Index class itself works like Index() (used to crash when the store was opened). """

    @Entity(model="index")
    class Item:
        id = Id
        name = String(index=Index)

    store = _open(tmp_path, Item)
    box = store.box(Item)
    box.put(Item(name="foo"))
    assert box.query(Item.name.equals("foo")).build().count() == 1
    store.close()
    assert _json_flags(tmp_path)["name"] == OBXPropertyFlags_INDEXED | OBXPropertyFlags_INDEX_HASH


@pytest.mark.parametrize("index", [True, "hash", IndexType.HASH, HnswIndex])
def test_index_invalid_arg(index):
    with pytest.raises(TypeError, match="index must be an Index"):
        String(index=index)


def test_docstring_examples(tmp_path):
    """ The examples of the @Entity and Box.query() docstrings work. """
    import re
    import textwrap
    import objectbox

    # @Entity: defines MyEntity (with an indexed name); add an age for the query example
    doc = "\n".join(line.rstrip() for line in objectbox.Entity.__doc__.splitlines())
    example = doc.split("Example::")[1].split("\n\n")[1]
    example = textwrap.dedent(example).replace("@Entity()", '@Entity(model="docstring")')
    example = example.replace("date_created = Date", "date_created = Date\n    age = Int32")
    namespace = dict(vars(objectbox))
    exec(example, namespace)
    MyEntity = namespace["MyEntity"]
    store = _open(tmp_path, MyEntity)
    box = store.box(MyEntity)
    box.put([MyEntity(name="Johnny", age=30), MyEntity(name="Johnny", age=20), MyEntity(name="Jim", age=40)])

    # Box.query()
    statements = re.findall(r"``(query = box\.query\(.*\)\.build\(\))``", objectbox.Box.query.__doc__)
    assert len(statements) == 2
    namespace.update(box=box)
    exec(statements[0], namespace)
    assert [o.age for o in namespace["query"].find()] == [30, 20]
    exec(statements[1], namespace)
    assert [o.age for o in namespace["query"].find()] == [30]
    store.close()
