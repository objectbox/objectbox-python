ObjectBox Python API
====================
[ObjectBox](https://objectbox.io) is a superfast database for objects, now also available for Python (3.4+) with a simple CRUD API.
And because it's an embedded database, there's no setup required.
 
## Table of Contents:
- [Getting Started](#getting-started)
   - [Model IDs and UIDs](#model-ids-and-uids)
   - [model.py](#modelpy)
- [Using ObjectBox](#using-objectbox)
- [Some features](#some-features)
- [Coming in the future](#coming-in-the-future)
- [Help wanted](#help-wanted)
- [Feedback](#feedback)
- [License](#license)

---

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
To learn more, see [ObjectBox Java documentation](https://docs.objectbox.io/advanced/meta-model-ids-and-uids)

#### model.py

```python
from objectbox.model import *

@Entity(id=1, uid=1)
class Person:
    id = Id(id=1, uid=1001)
    name = Property(str, id=2, uid=1002)
    is_enabled = Property(bool, id=3, uid=1003)
    # int can be stored with 64 (default), 32, 16 or 8 bit precision.
    int64 = Property(int, id=4, uid=1004)
    int32 = Property(int, type=PropertyType.int, id=5, uid=1005)
    int16 = Property(int, type=PropertyType.short, id=6, uid=1006)
    int8 = Property(int, type=PropertyType.byte, id=7, uid=1007)
    # float can be stored with 64 or 32 (default) bit precision.
    float64 = Property(float, id=8, uid=1008)
    float32 = Property(float, type=PropertyType.float, id=9, uid=1009)
    byte_array = Property(bytes, id=10, uid=1010)
    # Regular properties are not stored.
    transient = ""
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
model.entity(Person, last_property_id=objectbox.model.IdUid(10, 1010))
model.last_entity_id = objectbox.model.IdUid(1, 1)
store = objectbox.Store(model=model, directory="db")

# Open the box of "Person" entity. This can be called many times but you can also pass the variable around
box = objectbox.Box(ob, Person)

person = Person()
person.name = "Joe Green"
id = box.put(person)  # Create
person = box.get(id)  # Read
person.name = "Joe Black"
box.put(person)       # Update
box.remove(person)    # Delete
```

Additionally, see the [TaskList example app](https://github.com/objectbox/objectbox-python/tree/main/example). After checking out this repository to run the example:
```
// Set up virtual environment, download ObjectBox libraries
make depend

// Activate virtual environment...
// ...on Linux
source .venv/bin/activate
// ...on Windows
.venv\Scripts\activate

// Run the example
python3 -m example

// Once done, leave the virtual environment
deactivate
```

For more information and code examples, see the tests folder. The docs for other languages may also help you understand the basics.

* ObjectBox Java/Dart/Flutter - https://docs.objectbox.io
* ObjectBox Go - https://golang.objectbox.io
* ObjectBox Swift - https://swift.objectbox.io

Some features
-------------
* Automatic transactions (ACID compliant)
* Bulk operations
* Vector types, e.g. for AI vector embeddings
* Platforms supported with native speed:
  * Linux x86-64 (64-bit)
  * Linux ARMv6hf (e.g. Raspberry PI Zero)
  * Linux ARMv7hf (e.g. Raspberry PI 3; available only on request)
  * Linux ARMv8   (e.g. Raspberry PI 4)
  * MacOS x86-64 and arm64 (Intel 64-bit and Apple Silicon)
  * Windows x86-64 (64-bit)

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
ObjectBox for Python is still in an early stage with limited feature set (compared to our other supported languages).
To bring all these features to Python, we're asking the community to help out. PRs are more than welcome!
The ObjectBox team will try its best to guide you and answer questions.
See [CONTRIBUTING.md](https://github.com/objectbox/objectbox-python/blob/main/CONTRIBUTING.md) to get started.

Feedback
--------
Also, please let us know your feedback by opening an issue: for example, if you experience errors or if you have ideas
for how to improve the API. Thanks!

License
-------

```text
Copyright 2019-2024 ObjectBox Ltd. All rights reserved.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
```
