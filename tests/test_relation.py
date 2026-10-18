import json
import os

import pytest

from objectbox import *
from objectbox.model import *
from objectbox.model.properties import PropertyType


def _define():
    @Entity(model="relation")
    class Customer:
        id = Id
        name = String

    @Entity(model="relation")
    class Order:
        id = Id
        text = String
        customer_id = Relation(Customer)

    @Entity(model="relation")
    class Node:
        id = Id
        name = String
        parent_id = Relation("Node")  # To itself, by name

    return Customer, Order, Node


def _open(tmp_path, *entities) -> Store:
    model = Model()
    for entity in entities:
        model.entity(entity)
    return Store(model=model, directory=str(tmp_path / "db"), model_json_file=str(tmp_path / "model.json"))


def _json_props(tmp_path, entity_name: str):
    with open(str(tmp_path / "model.json")) as file:
        doc = json.load(file)
    return {p["name"]: p for e in doc["entities"] if e["name"] == entity_name for p in e["properties"]}


def test_relation_model(tmp_path):
    Customer, Order, Node = _define()
    store = _open(tmp_path, Customer, Order, Node)
    prop = _json_props(tmp_path, "Order")["customerId"]
    assert prop["type"] == PropertyType.relation == 11
    assert prop["flags"] == 520  # INDEXED | INDEX_PARTIAL_SKIP_ZERO, as in the other ObjectBox languages
    assert prop["relationTarget"] == "Customer"
    assert prop["indexId"] == str(Order.customer_id.index.iduid)
    assert _json_props(tmp_path, "Node")["parentId"]["relationTarget"] == "Node"
    store.close()

    # Reopening with the same model JSON file keeps the IDs
    Customer, Order, Node = _define()
    store = _open(tmp_path, Customer, Order, Node)
    assert _json_props(tmp_path, "Order")["customerId"] == prop
    store.close()


def test_relation_put_get_query(tmp_path):
    Customer, Order, Node = _define()
    store = _open(tmp_path, Customer, Order, Node)
    customer_box = store.box(Customer)
    order_box = store.box(Order)
    joe = customer_box.put(Customer(name="Joe"))
    ann = customer_box.put(Customer(name="Ann"))
    o1 = order_box.put(Order(text="o1", customer_id=joe))
    o2 = order_box.put(Order(text="o2", customer_id=ann))
    o3 = order_box.put(Order(text="o3"))  # No customer
    o4 = order_box.put(Order(text="o4", customer_id=None))  # Null

    assert order_box.get(o1).customer_id == joe
    assert order_box.get(o3).customer_id == 0
    assert order_box.get(o4).customer_id == 0

    assert order_box.query(Order.customer_id.equals(joe)).build().find_ids() == [o1]
    assert order_box.query(Order.customer_id.equals(0)).build().find_ids() == [o3]
    assert order_box.query(Order.customer_id.is_null()).build().find_ids() == [o4]
    assert order_box.query(Order.customer_id.one_of([joe, ann])).build().find_ids() == [o1, o2]
    query = order_box.query(Order.customer_id.equals(joe)).build()
    assert query.set_parameter(Order.customer_id, ann).find_ids() == [o2]

    node_box = store.box(Node)
    root = node_box.put(Node(name="root"))
    child = node_box.put(Node(name="child", parent_id=root))
    assert node_box.get(child).parent_id == root
    store.close()


def test_relation_target_removed(tmp_path):
    """ Removing the target object resets the relation to 0. """
    Customer, Order, Node = _define()
    store = _open(tmp_path, Customer, Order, Node)
    customer_box = store.box(Customer)
    order_box = store.box(Order)
    joe = customer_box.put(Customer(name="Joe"))
    o1 = order_box.put(Order(text="o1", customer_id=joe))
    customer_box.remove(joe)
    assert order_box.get(o1).customer_id == 0
    assert order_box.query(Order.customer_id.equals(joe)).build().count() == 0
    store.close()


def test_relation_target_invalid(tmp_path):
    with pytest.raises(TypeError, match="Relation target must be an entity"):
        Relation(object)

    @Entity(model="relation")
    class Order:
        id = Id
        customer_id = Relation("Nope")

    with pytest.raises(ValueError, match="Relation Order.customer_id targets entity \"Nope\", which is not in the model"):
        _open(tmp_path, Order)
    assert not os.path.exists(str(tmp_path / "model.json"))  # Not written


def test_relation_from_int64(tmp_path):
    """ An existing Int64 property can not become a Relation (different type in the database). """

    @Entity(model="relation")
    class Customer:
        id = Id

    @Entity(model="relation")
    class Order:
        id = Id
        customer_id = Int64(index=Index())

    _open(tmp_path, Customer, Order).close()

    @Entity(model="relation")
    class Order:
        id = Id
        customer_id = Relation(Customer)

    with pytest.raises(ValueError, match="Order.customer_id mismatches property found in JSON file: OBX type 11 != "
                                         "OBX type 6"):
        _open(tmp_path, Customer, Order)
