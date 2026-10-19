ObjectBox Python
================
[ObjectBox](https://objectbox.io) Python is a lightweight yet powerful on-device object and vector database.
Store Python objects and vectors directly with an easy-to-use CRUD API while enjoying exceptional speed and efficiency.
And because it's an embedded database, there's no setup required.

Its advanced vector search empowers on-device AI applications including RAG, generative AI, and similarity searches.

The ObjectBox database delivers high-performance on commodity hardware - locally, on-device.
On top, as an offline-first solution, ObjectBox makes sure your app reliably works offline as well as online
(via [Sync](https://objectbox.io/sync/)).

> **Upgrading from ObjectBox 4.x (or earlier) with pip? Uninstall `objectbox` first**, then install the new version;
> an in-place `pip install --upgrade objectbox` breaks the installation. See [Updating from 4.x](#updating-from-4x).

_Table of Contents_

- [Feature Highlights](#feature-highlights)
- [Coding with AI agents](#coding-with-ai-agents)
- [Code Example (CRUD - Create, Read, Update, Delete)](#code-example-crud-create-read-update-delete)
- [Getting Started](#getting-started)
- [Help wanted](#help-wanted)
- [Feedback](#feedback)
- [License](#license)

Feature Highlights
------------------

🏁 **On-device vector database** - for AI apps that work any place.\
🏁 **High performance** - superfast response rates enabling real-time applications.
   [Faster than any ORM](https://github.com/objectbox/python-orm-benchmarks/).\
🪂 **ACID compliant** - Atomic, Consistent, Isolated, Durable.\
🌱 **Scalable** - grows with your app, handling millions of objects with ease.\
💚 **Sustainable** - frugal on CPU, Memory and battery / power use, reducing CO2 emissions.\
💐 **[Queries](https://docs.objectbox.io/queries)** - filter data as needed, even across relations.\
💻 **Multiplatform** - Get native speed on your favorite platforms.\
* Linux x86-64 (64-bit)
* Linux ARMv7hf (e.g. Raspberry PI 3)
* Linux ARMv8   (e.g. Raspberry PI 4, 5, etc.)
* MacOS x86-64 and arm64 (Intel 64-bit and Apple Silicon)
* Windows x86-64 (64-bit)
* Windows ARM64

Coding with AI agents
---------------------

Using an AI coding agent (Claude Code, Codex, Cursor, ...)?
Install the [ObjectBox agent skill](https://github.com/objectbox/objectbox-skills):
it teaches the agent the ObjectBox how-tos and common pitfalls.

```shell
npx skills add objectbox/objectbox-skills
```

In Claude Code, also via the plugin marketplace:
`/plugin marketplace add objectbox/objectbox-skills`, then `/plugin install objectbox@objectbox-skills`.

Agents load the skill when a task involves ObjectBox. To make sure yours always uses it, say so in your project's agent
instructions (e.g. `AGENTS.md` or `CLAUDE.md`):

```markdown
This project uses ObjectBox (Python). For any code that touches the database, its entities or objectbox-model.json,
use the objectbox skill and follow its Python reference.
```

Code Example: CRUD (Create, Read, Update, Delete)
-------------------------------------------------

What does using ObjectBox in Python look like?

```python
from objectbox import Entity, Id, Store, String

@Entity()
class Person:
    id = Id
    name = String

# The ObjectBox Store represents a database; keep it around...
store = Store()

# Get a box for the "Person" entity; a Box is the main interaction point with objects and the database.
box = store.box(Person)

person = Person(name = "Joe Green")
id = box.put(person)  # Create
person = box.get(id)  # Read
person.name = "Joe Black"
box.put(person)       # Update
box.remove(person)    # Delete
```

Ready for more? Check the [example folder](https://github.com/objectbox/objectbox-python/tree/main/example).

Getting started
---------------
Latest version: 5.0.0

To install ObjectBox, run this:

```bash
pip install objectbox
```
Now you are ready to use ObjectBox in your Python project.

To update to the latest version (from version 5 on), run `pip install --upgrade objectbox`.

### Updating from 4.x

**Uninstall `objectbox` first**, then install the new version:

```bash
pip uninstall objectbox
pip install objectbox
```

Since version 5, the Python code is in the package `objectbox-api`, which `objectbox` installs along with the
ObjectBox library (package `objectbox-clib`). An in-place `pip install --upgrade objectbox` from 4.x breaks the
installation: pip installs the new packages first, then removes the files of the previous `objectbox` version, which
are now part of `objectbox-api`. `import objectbox` fails afterwards, e.g. with
`ImportError: cannot import name 'Store' from 'objectbox' (unknown location)` or a `ModuleNotFoundError`;
running the upgrade again does not fix it. To repair such an installation, run:
`pip install --force-reinstall --no-deps objectbox-api`.
Fresh installs and upgrades via uv (e.g. `uv pip install --upgrade objectbox`) are not affected.
For [ObjectBox Sync](#sync), install `objectbox-sync` instead of `objectbox` (also uninstall `objectbox` first).

### Next steps

Head over to the **[ObjectBox documentation](https://docs.objectbox.io)**
and learn how to setup your first entity classes.

### Sync

[ObjectBox Sync](https://objectbox.io/sync/) synchronizes data with an ObjectBox Sync server (and other devices).
It requires the Sync variant of the ObjectBox library: install the package `objectbox-sync` **instead of** `objectbox`
(not in addition; it provides the same Python API and module `objectbox`, plus the Sync variant of the library):

```bash
pip uninstall objectbox  # If installed
pip install --upgrade objectbox-sync
```

Enable Sync for an entity with `@SyncEntity()` (together with `@Entity()`) and start a Sync client for the store:

```python
from objectbox import Entity, Id, String, Store, SyncEntity
from objectbox.sync import Sync, SyncCredentials

@SyncEntity()
@Entity()
class Task:
    id = Id
    text = String

store = Store()
client = Sync.client(store, "ws://127.0.0.1:9999", SyncCredentials.none())
client.start()  # Connects and syncs in the background; closed with the store
```

### Examples

Do you prefer to dive right into working examples?
We have you covered in the [example](https://github.com/objectbox/objectbox-python/tree/main/example) folder.
It comes with a task list application and a vector search example using cities (CLI app and Jupyter notebook).
For AI developers , we provide an "ollama" example, which integrates a local LLM (via [ollama](https://ollama.com))
with ObjectBox to manage and search embeddings effectively.

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
Copyright 2019-2026 ObjectBox Ltd. All rights reserved.

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
