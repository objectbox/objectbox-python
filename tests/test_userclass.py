from objectbox import *
from objectbox.model import *
from objectbox.model.idsync import sync_model

def test_userclass():
    @Entity()
    class Person:
        id = Id()
        firstName = String()
        lastName = String()

        def __init__(self):
            self.counter = 0

        def fullname(self):
            return f"{self.firstName} {self.lastName}"

        def tick(self):
            self.counter += 1

    model = Model()
    model.entity(Person)
    sync_model(model)
    dbpath = "testdb"
    Store.remove_db_files(dbpath)

    store = Store(model=model, directory=dbpath)
    box = store.box(Person)
    id_alice = box.put(Person(firstName="Alice", lastName="Adkinson"))
    box.put(Person(firstName="Bob", lastName="Bowman"))
    box.put(Person(firstName="Cydia", lastName="Cervesa"))
    assert box.count() == 3
    alice = box.get(id_alice)
    assert alice.fullname() == "Alice Adkinson"
    assert alice.counter == 0
    alice.tick()
    alice.tick()
    assert alice.counter == 2

    alice = box.get(id_alice)
    assert alice.counter == 0

    id_empty = box.put(Person())
    empty = box.get(id_empty)
    assert empty.fullname() == " "
