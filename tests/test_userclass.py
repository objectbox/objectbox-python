from objectbox import *
from objectbox.model import *

def test_userclass():
    
    @Entity(id=1, uid=1)
    class Person:
        id = Id(id=1, uid=1001)
        firstName = Property(str, id=2, uid=1002)
        lastName = Property(str, id=3, uid=1003)
        def __init__(self):
            self.counter = 0
        def fullname(self):
            return f"{self.firstName} {self.lastName}"
        def tick(self):
            self.counter += 1
    
    model = Model()
    model.entity(Person, last_property_id=IdUid(3, 1003))
    model.last_entity_id = IdUid(1,1)
    dbpath = "testdb"
    Store.remove_db_files(dbpath)
    store = Store(model = model, directory = dbpath)
    box = store.box(Person)
    id_alice = box.put( Person(firstName="Alice", lastName="Adkinson")) 
    id2 = box.put( Person(firstName="Bob", lastName="Bowman")) 
    id3 = box.put( Person(firstName="Cydia", lastName="Cervesa"))
    assert box.count() == 3
    alice = box.get(id_alice)
    assert alice.fullname() == "Alice Adkinson"
    assert alice.counter == 0
    alice.tick()
    alice.tick()
    assert alice.counter == 2
