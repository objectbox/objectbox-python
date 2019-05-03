ObjectBox Python API
================
ObjectBox is a superfast database for objects, now also available for Python.

ObjectBox persists your native Python classes using a simple CRUD API:

```python
# model.py
@Entity(id=1, uid=1)
class Person:
    id = Id(id=1, uid=1001)
    first_name = Property(str, id=2, uid=1002)
    last_name = Property(str, id=3, uid=1003)

# program.py
box = objectbox.Box(ob, Person)
 
id = box.put(Person(first_name="Joe", last_name="Green"))  # Create
person = box.get(id)  # Read
person.last_name = "Black"
box.put(person)       # Update
box.remove(person)    # Delete
```

For more information and code examples see the tests folder.

Latest release: v0.1.0

Some features
-------------
* automatic transactions (ACID compliant)
* bulk operations

# Coming soon
The goodness you know from other language-bindings ObjectBox has, e.g.:
* model management (no need to manually set id/uid)
* automatic model migration (no schema upgrade scripts etc.)
* powerful queries
* relations (to-one, to-many)
* asynchronous operations
* secondary indexes 

Installation
------------
To get started with ObjectBox you can get the repository code. 
This repo uses `virtualenv` when installing packages so in case you don't have it yet: `pip install virtualenv`.

The main prerequisite to using the Python APIs is the ObjectBox binary library (.so, .dylib, .dll depending on your  platform) which actually implements the database functionality. 
In the [ObjectBox C repository](https://github.com/objectbox/objectbox-c), you should find a download.sh script you can run.
Follow the instructions and type Y when it asks you if it should install the library.
```bash
bash <(curl https://raw.githubusercontent.com/objectbox/objectbox-c/master/download.sh)
```

You can run `make test` to make sure everything works as expected.

Required Python version: 3.4+

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

