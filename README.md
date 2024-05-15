ObjectBox Python
================
[ObjectBox](https://objectbox.io) Python is a lightweight yet powerful on-device database & vector database.
Store Python objects and vectors directly with an easy-to-use CRUD API while enjoying exceptional speed and efficiency.
And because it's an embedded database, there's no setup required.

Its advanced vector search empowers AI for a variety of applications, including RAG AI, generative AI,
and similarity searches.

Designed for high performance, the ObjectBox database runs locally on-device.
As an offline-first solution, ObjectBox makes sure your app reliably works offline as well as online
(via [Sync](https://objectbox.io/sync/)).

_Table of Contents_

- [Feature Highlights](#feature-highlights)
- [Code Example (CRUD - Create, Read, Update, Delete)](#code-example-crud---create-read-update-delete)
- [Getting Started](#getting-started)
- [Alpha Notes](#alpha-notes)
- [Help wanted](#help-wanted)
- [Feedback](#feedback)
- [License](#license)

Feature Highlights
------------------

🏁 **On-device vector database** - for AI apps that work any place.\
🏁 **High performance** - superfast response rates enabling real-time applications.\
🪂 **ACID compliant** - Atomic, Consistent, Isolated, Durable.\
🌱 **Scalable** - grows with your app, handling millions of objects with ease.\
💚 **Sustainable** - frugal on CPU, Memory and battery / power use, reducing CO2 emissions.\
💐 **[Queries](https://docs.objectbox.io/queries)** - filter data as needed, even across relations.\
💻 **Multiplatform** - Get native speed on your favorite platforms.\
* Linux x86-64 (64-bit)
* Linux ARMv6hf (e.g. Raspberry PI Zero)
* Linux ARMv7hf (e.g. Raspberry PI 3)
* Linux ARMv8   (e.g. Raspberry PI 4, 5, etc.)
* MacOS x86-64 and arm64 (Intel 64-bit and Apple Silicon)
* Windows x86-64 (64-bit)

#### Code Example (CRUD - Create, Read, Update, Delete)

What does using ObjectBox in Python look like?

```python
import objectbox

# from mypackage.model import Person

# The ObjectBox Store represents a database; keep it around...
store = objectbox.Store(model=model)

# Get a box for the "Person" entity; a Box is the main interaction point with objects and the database.
box = store.box(Person)

person = Person()
person.name = "Joe Green"
id = box.put(person)  # Create
person = box.get(id)  # Read
person.name = "Joe Black"
box.put(person)       # Update
box.remove(person)    # Delete
```

Getting started
---------------
Latest version: 4.0.0a0 (2024-05-15)

To install or update the latest version of ObjectBox, run this:

```bash
pip install --upgrade --pre objectbox  # "--pre" because you want to get the 4.0.0 alpha version
```
Now you are ready to use ObjectBox in your Python project.

Head over to the **[ObjectBox documentation](https://docs.objectbox.io)**
and learn how to setup your first entity classes.

### Examples

Do you prefer to dive right into working examples?
We have you covered in the [example](example/) folder.
It comes with a task list application and a vector search example using cities.
Additionally, for AI enthusiasts, we provide an "ollama" example,
which integrates a local LLM (via [ollama](https://ollama.com))
with ObjectBox to manage and search embeddings effectively.

Alpha Notes
-----------
While ObjectBox Python is powered by a rock stable core written in C/C++, we label our Python binding still "alpha."
We do this to manage expectations as some quality of life improvements are yet to come to our Python binding.
This is mostly about "model management," which still requires you to do some manual coding setup, e.g. for model IDs.
The final release will take care of this for you automatically.

Help wanted
-----------
ObjectBox for Python is open to contributions.
The ObjectBox team will try its best to guide you and answer questions.
See [CONTRIBUTING.md](https://github.com/objectbox/objectbox-python/blob/main/CONTRIBUTING.md) to get started.

Feedback
--------
We are looking for your feedback!
Please let us know what you think about ObjectBox for Python and how we can improve it.

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
