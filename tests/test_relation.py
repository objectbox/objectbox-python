import json
import os

import pytest

from objectbox import *
from objectbox.model import *
from objectbox.model.properties import PropertyType
from objectbox.exceptions import IllegalArgumentError, IllegalStateError


def _define():
    @Entity(model="relation")
    class Company:
        id = Id
        name = String

    @Entity(model="relation")
    class Customer:
        id = Id
        name = String
        company_id = Relation(Company)

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

    return Company, Customer, Order, Node


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
    Company, Customer, Order, Node = _define()
    store = _open(tmp_path, Company, Customer, Order, Node)
    prop = _json_props(tmp_path, "Order")["customerId"]
    assert prop["type"] == PropertyType.relation == 11
    assert prop["flags"] == 520  # INDEXED | INDEX_PARTIAL_SKIP_ZERO, as in the other ObjectBox languages
    assert prop["relationTarget"] == "Customer"
    assert prop["indexId"] == str(Order.customer_id.index.iduid)
    assert _json_props(tmp_path, "Node")["parentId"]["relationTarget"] == "Node"
    store.close()

    # Reopening with the same model JSON file keeps the IDs
    Company, Customer, Order, Node = _define()
    store = _open(tmp_path, Company, Customer, Order, Node)
    assert _json_props(tmp_path, "Order")["customerId"] == prop
    store.close()


def test_relation_put_get_query(tmp_path):
    Company, Customer, Order, Node = _define()
    store = _open(tmp_path, Company, Customer, Order, Node)
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
    Company, Customer, Order, Node = _define()
    store = _open(tmp_path, Company, Customer, Order, Node)
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


@pytest.fixture
def linked(tmp_path):
    """ Companies Acme and Bolt; customers Joe (Acme), Ann (Bolt) and Max (none); orders o1 (Joe), o2 and o3 (Ann),
    o4 (none); nodes root <- child <- grandchild. """
    Company, Customer, Order, Node = _define()
    store = _open(tmp_path, Company, Customer, Order, Node)
    company_box, customer_box, order_box = store.box(Company), store.box(Customer), store.box(Order)
    acme, bolt = company_box.put(Company(name="Acme")), company_box.put(Company(name="Bolt"))
    joe = customer_box.put(Customer(name="Joe", company_id=acme))
    ann = customer_box.put(Customer(name="Ann", company_id=bolt))
    max_ = customer_box.put(Customer(name="Max"))
    orders = [order_box.put(order) for order in [Order(text="o1", customer_id=joe), Order(text="o2", customer_id=ann),
                                                 Order(text="o3", customer_id=ann), Order(text="o4")]]
    node_box = store.box(Node)
    root = node_box.put(Node(name="root"))
    child = node_box.put(Node(name="child", parent_id=root))
    node_box.put(Node(name="grandchild", parent_id=child))
    yield store, (Company, Customer, Order, Node), dict(acme=acme, bolt=bolt, joe=joe, ann=ann, max=max_,
                                                        orders=orders)
    store.close()


def _texts(query):
    return sorted(o.text for o in query.find())


def _names(query):
    return sorted(o.name for o in query.find())


def test_link(linked):
    store, (Company, Customer, Order, Node), ids = linked
    order_box = store.box(Order)

    qb = order_box.query()
    qb.link(Order.customer_id, Customer.name.equals("Ann"))
    assert _texts(qb.build()) == ["o2", "o3"]

    # Combined with conditions on the query's entity (AND)
    qb = order_box.query(Order.text.equals("o3") | Order.text.equals("o1"))
    qb.link(Order.customer_id, Customer.name.equals("Ann"))
    assert _texts(qb.build()) == ["o3"]

    # Combined conditions on the target
    qb = order_box.query()
    qb.link(Order.customer_id, Customer.name.equals("Ann") | Customer.name.equals("Joe"))
    assert _texts(qb.build()) == ["o1", "o2", "o3"]

    # Over two relations: orders of customers of company Acme
    qb = order_box.query()
    qb.link(Order.customer_id).link(Customer.company_id, Company.name.equals("Acme"))
    assert _texts(qb.build()) == ["o1"]

    # To the entity itself: nodes whose parent is "root", and whose grandparent is "root"
    node_box = store.box(Node)
    qb = node_box.query()
    qb.link(Node.parent_id, Node.name.equals("root"))
    assert _names(qb.build()) == ["child"]
    qb = node_box.query()
    qb.link(Node.parent_id).link(Node.parent_id, Node.name.equals("root"))
    assert _names(qb.build()) == ["grandchild"]


def test_backlink(linked):
    store, (Company, Customer, Order, Node), ids = linked
    customer_box = store.box(Customer)

    qb = customer_box.query()
    qb.backlink(Order.customer_id, Order.text.equals("o2") | Order.text.equals("o3"))
    assert _names(qb.build()) == ["Ann"]  # Once, although two orders match

    qb = customer_box.query()
    qb.backlink(Order.customer_id)  # Customers with any order
    assert _names(qb.build()) == ["Ann", "Joe"]

    qb = customer_box.query()
    qb.backlink(Order.customer_id, Order.text.equals("o4"))  # o4 has no customer
    assert qb.build().find() == []

    # Over two relations: companies with an order "o1"
    qb = store.box(Company).query()
    qb.backlink(Customer.company_id).backlink(Order.customer_id, Order.text.equals("o1"))
    assert _names(qb.build()) == ["Acme"]

    # Mixed: orders of customers whose company has a customer named "Joe"
    qb = store.box(Order).query()
    qb.link(Order.customer_id).link(Customer.company_id).backlink(Customer.company_id, Customer.name.equals("Joe"))
    assert _texts(qb.build()) == ["o1"]

    # To the entity itself: nodes with a child named "grandchild"
    qb = store.box(Node).query()
    qb.backlink(Node.parent_id, Node.name.equals("grandchild"))
    assert _names(qb.build()) == ["child"]


def test_link_parameters(linked):
    store, (Company, Customer, Order, Node), ids = linked
    qb = store.box(Order).query(Order.text.not_equals("o3"))
    qb.link(Order.customer_id, Customer.name.equals("Ann") & Customer.id.one_of([ids["ann"]]).alias("ids"))
    query = qb.build()
    assert _texts(query) == ["o2"]
    assert _texts(query.set_parameter(Customer.name, "Joe")) == []
    assert _texts(query.set_parameter_alias("ids", [ids["joe"], ids["ann"]])) == ["o1"]
    assert _texts(query.set_parameter(Order.text, "o1")) == []  # The query's entity: text != "o1"
    assert _texts(query.set_parameter(Customer.name, "Ann")) == ["o2", "o3"]


def test_link_invalid(linked):
    store, (Company, Customer, Order, Node), ids = linked
    qb = store.box(Order).query()
    with pytest.raises(TypeError, match="Expected a Relation property"):
        qb.link(Order.text)
    with pytest.raises(IllegalArgumentError, match="relation Customer.company_id is not a property of entity Order"):
        qb.link(Customer.company_id)
    with pytest.raises(IllegalArgumentError, match="relation Customer.company_id targets entity Company, not Order"):
        qb.backlink(Customer.company_id)

    linked_qb = qb.link(Order.customer_id, Customer.name.equals("Ann"))
    with pytest.raises(IllegalStateError, match=r"build\(\) is not supported on the builder of a linked entity"):
        linked_qb.build()
    with pytest.raises(IllegalStateError, match=r"order\(\) is not supported on the builder of a linked entity"):
        linked_qb.order(Customer.name)
    assert _texts(qb.build()) == ["o2", "o3"]
