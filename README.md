ObjectBox Python API
====================
ObjectBox is a superfast database for objects, now also available for Python with a simple CRUD API.

* Python version: 3.4+
* Platforms supported: 
    * Linux 64-bit
    * Linux ARMv6hf (e.g. Raspberry PI Zero)
    * Linux ARMv7hf (e.g. Raspberry PI 3)
    * MacOS 64-bit
    * Windows 64-bit

Getting started
---------------
First of all, install the latest version:
```bash
pip install --upgrade objectbox
```

To start using ObjectBox as a storage for your data, you need to define your model first. 
The model consists of Python classes annotated with `@Entity` decorator. 

### Model IDs and UIDs
Each Entity has to have an ID (unique among entities). 
Properties need an ID as well (unique inside one Entity). 
Both Entities and Properties must also have an UID, which is a globally unique identifier.

For other ObjectBox supported languages, the binding takes care of assigning these IDs/UIDs but this feature is not yet implemented for Python.
To learn more, see ObjectBox Java documentation: https://docs.objectbox.io/advanced/meta-model-ids-and-uids

#### model.py
```python
from objectbox.model import *

@Entity(id=1, uid=1)
class Person:
    id = Id(id=1, uid=1001)
    first_name = Property(str, id=2, uid=1002)
    last_name = Property(str, id=3, uid=1003)
```

### Using ObjectBox
To actually use the database, you launch (or "build") it with the model you've just defined.
Afterwards, you can reuse the instance (`ob` in the example below) and use it to access "Entity Boxes" which hold your objects.
  
#### program.py
```python
import objectbox
# from mypackage.model import Person

# Configure ObjectBox: should be done only once in the whole program and the "ob" variable should be kept around
model = objectbox.Model()
model.entity(Person, last_property_id=objectbox.model.IdUid(3, 1003))
model.last_entity_id = objectbox.model.IdUid(1, 1)
ob = objectbox.Builder().model(model).directory("db").build()

# Open the box of "Person" entity. This can be called many times but you can also pass the variable around
box = objectbox.Box(ob, Person)
 
id = box.put(Person(first_name="Joe", last_name="Green"))  # Create
person = box.get(id)  # Read
person.last_name = "Black"
box.put(person)       # Update
box.remove(person)    # Delete
```

For more information and code examples, see the tests folder. The docs for other languages may also help you understand the basics.

* ObjectBox Java = https://docs.objectbox.io
* ObjectBox Go - https://golang.objectbox.io
* ObjectBox Swift - https://swift.objectbox.io
* ObjectBox Dart/Flutter - https://github.com/objectbox/objectbox-dart

Some features
-------------
* automatic transactions (ACID compliant)
* bulk operations

Coming in the future
--------------------
The goodness you know from the other ObjectBox language-bindings, e.g.,

* model management (no need to manually set id/uid)
* automatic model migration (no schema upgrade scripts etc.)
* powerful queries
* relations (to-one, to-many)
* asynchronous operations
* secondary indexes

Help wanted
-----------
ObjectBox for Python is still in an early stage with limited feature set (compared to other languages). 
To bring all these features to Python, we're asking the community to help out. PRs are more than welcome! 
The ObjectBox team will try its best to guide you and answer questions. See [CONTRIBUTING.md](CONTRIBUTING.md) to get started

Feedback
--------
Also, please let us know your feedback by opening an issue: for example, if you experience errors or if you have ideas 
for how to improve the API. Thanks!

License
-------
    Copyright 2019 ObjectBox Ltd. All rights reserved.
    
    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at
    
        http://www.apache.org/licenses/LICENSE-2.0
    
    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.

