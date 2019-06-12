ObjectBox Python API
====================
ObjectBox is a superfast database for objects, now also available for Python with a simple CRUD API.

* Latest release: v0.1.0
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

Some features
-------------
* automatic transactions (ACID compliant)
* bulk operations

Coming in the future
-------------
The goodness you know from the other ObjectBox language-bindings, e.g.,
* model management (no need to manually set id/uid)
* automatic model migration (no schema upgrade scripts etc.)
* powerful queries
* relations (to-one, to-many)
* asynchronous operations
* secondary indexes 

Contributing
------------
Currently, the Python binding is in its very early stages and lots of features available in other languages are missing.
If you have a request for a specific feature, please open an issue. If you want to contribute, please feel free to open a PR.
In case it's a non-obvious contribution it might be better to discuss and align first in an issue. 

This repo uses `virtualenv` when installing packages so in case you don't have it yet: `pip install virtualenv`.

The main prerequisite to using the Python APIs is the ObjectBox binary library (.so, .dylib, .dll depending on your  platform) which actually implements the database functionality.

The library should be placed in the `objectbox/lib/[architecture]/` folder of the checked out repository.

### Getting ObjectBox C-API library from pip
The easiest way is to get all the binaries from the latest release in PyPI.
```bash
pip download objectbox
unzip objectbox*.whl
cp -r objectbox/lib [/path/to/your/git/objectbox/checkout]/objectbox/  
```  

### Downloading from the ObjectBox-C release
Alternatively, you can get the appropriate release from the ObjectBox-C repository.
However, you need to pay attention to the required version - see `required_version` in `objectbox/c.py`.
In the [ObjectBox C repository](https://github.com/objectbox/objectbox-c), you should find a download.sh script you can run.


```bash
wget https://raw.githubusercontent.com/objectbox/objectbox-c/master/download.sh
chmod +x download.sh
# replace [required_version] with the appropriate string then type N when the script asks about installing the library
./download.sh [required_version]
cp lib/*objectbox* [/path/to/your/git/objectbox/checkout]/objectbox/lib/$(uname -m)/
```

You can run `make test` to make sure everything works as expected.
You can also try `make benchmark` to measure the CRUD performance on your machine.

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

