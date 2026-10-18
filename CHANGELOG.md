ObjectBox Python ChangeLog
==========================

5.0.0b1
-------

ObjectBox Python 5.0 is a massive update with many highlights:

* Performance: enable codegen to boost CRUD operations to speeds that beat any Python ORM
* Improved packaging: platform-specific wheels
* More powerful Query and Box operations with an easy-to-use API
* ObjectBox Sync to synchronize your data with a server and/or MongoDB

**Upgrading from 4.x with pip: uninstall `objectbox` first** (`pip uninstall objectbox`, then `pip install objectbox`).
An in-place `pip install --upgrade objectbox` would fail (e.g. "cannot import name 'Store' from 'objectbox' (unknown
location)"); repair via `pip install --force-reinstall --no-deps objectbox-api`. Fresh installs and uv are not affected.
As this is a beta version, add `--pre` to install it, e.g. `pip install --pre objectbox`.

### Performance

* Faster reads (get, queries): copying an object's data from the database takes ~0.4 µs instead of ~1 µs.
  Transactions (`read_tx()`, `write_tx()`, also used internally) have ~0.7 µs less overhead.
  Together, e.g. `box.get()` of a small object takes ~4.3 µs instead of ~6.9 µs (with the FlatBuffers codegen).
* Faster put of a single new object: its ID is assigned while putting, saving a call to reserve it (~0.3 µs)
* Faster import: `import objectbox` no longer imports numpy (also not via flatbuffers, which imports numpy) and takes
  about half the time. numpy is imported when needed, e.g. for vector properties or the first put or get.
  Importing numpy may start BLAS threads (OpenBLAS: one per CPU core) that busy-wait for ~0.1 s, slowing down
  short-lived processes. With the experimental FlatBuffers codegen (see below), entities without vector or flex
  properties never import numpy or flatbuffers.
* Faster opening of many stores, e.g. one store per user or agent. A model is synced with the model JSON file
  only once per process (also when given by name, e.g. the default model), saving about 0.1 ms per open.
  The new option `skip_model_sync` additionally opens existing stores with the schema stored in their database
  instead of checking it against the model, which halves the time to open (see its documentation for when to use it).
* Experimental: FlatBuffers codegen for putting objects, enabled via `objectbox.experimental.enable_flatbuffers_codegen()`
  (off by default; replaces the fast builder if that is enabled). Like the fast builder, but generates Python code per
  entity at its first put, which is again ~2x faster for small objects (~25x faster than the generic builder);
  putting 10,000 objects of the test entity ~5x faster than the generic builder.
  Codegen also reads objects (get, queries) with generated code, returning the same objects: ~3.5x faster per object
  for a small entity, ~8x faster for 21 properties.
  The code is compiled per process at the first put and first read of an entity (~2.8 ms for both with 38 properties);
  the new option `cache_dir` caches the compiled code for other processes (~0.5 ms then), e.g. for short-lived ones.
* Experimental: a fast FlatBuffers builder for putting objects, enabled via
  `objectbox.experimental.enable_fast_flatbuffers_builder()` (off by default). It produces the same bytes as before,
  with the layout precomputed per entity instead of using the generic `flatbuffers.Builder`; marshalling an object
  with a string and two numbers gets ~12x faster, putting 10,000 objects of the test entity ~4x faster.

### Installation and platforms

* Packaging: the Python code is now in the new package `objectbox-api` and the ObjectBox C library in the new package
  `objectbox-clib`; `objectbox` installs both (it contains no code itself). Install `objectbox` as before, but when
  upgrading from 4.x with pip, uninstall it first (see above).
* C library package `objectbox-clib`: there is a wheel for each platform, so only the library for your platform is
  downloaded (was: libraries for all platforms):
  Linux x86_64, aarch64 and armv7l (glibc 2.28+), macOS 11+ (universal) and Windows x64 and ARM64 (new).\
  **Breaking:** Linux ARMv6hf (e.g. Raspberry Pi Zero/1) is no longer supported, as PyPI does not support wheels for it.
* New platform: Windows ARM64 (64-bit ARM, e.g. Snapdragon-based devices)
* Linux: support 32-bit Python on a 64-bit kernel, e.g. Raspberry Pi OS 32-bit on a Raspberry Pi 4/5
  (64-bit kernel by default); this failed to load the library before.
* Requires Python 3.7 or newer (the package metadata claimed 3.4 before, but the code required 3.7 already)
* Update to ObjectBox C library 5.3.2 (was 4.0.0), see https://github.com/objectbox/objectbox-c/blob/main/CHANGELOG.md
* Dependency flatbuffers: any version from 24.3.25 on is accepted now (was pinned to 24.3.25); tested up to 25.12.19

### Query

* Order results via `QueryBuilder.order(property, flags)`, e.g. `box.query().order(Person.name).build()`;
  `OrderFlags` (exported by the top-level module) adjust the order, e.g. `DESCENDING` or `CASE_SENSITIVE`;
  `order_desc(property)` orders descending
* New "one of" conditions `String.one_of(values)` and, for integer properties, `one_of(values)` and
  `not_one_of(values)`; their values can be changed on a built query via `set_parameter()` (see below)
* New conditions `is_null()` and `is_not_null()` (e.g. `Task.text.is_null()`), also as `QueryBuilder.is_null()`
  and `not_null()`. Null values (put with `None`) do not match conditions on the default value, e.g. `equals("")`.
* `set_parameter(property, value)` and `set_parameter_alias(alias, value)` change the value of a condition;
  the property type decides how, e.g. a list sets the vector of a nearest neighbor search or the values of a
  "one of" condition, and `Date` properties also take a `datetime`. `set_parameters(property, a, b)` and
  `set_parameters_alias(alias, a, b)` change the two values of `between()`. New are also parameters for floating point
  and bytes properties, and `describe_parameters()`.\
  **Breaking:** the typed methods `set_parameter_string()`, `set_parameter_int()` and `set_parameter_vector_f32()` are
  removed; use `set_parameter()` instead, and `set_parameter_alias()` for their `set_parameter_alias_*()` variants.
* Fix `offset()` and `limit()` to return the query (as documented), e.g. for `query.offset(10).limit(5).find()`;
  they returned a C result code (int), so chaining failed
* The top-level module now also exports `Query`, `QueryBuilder`, `PropertyQueryCondition` and `HnswFlags`

### Box and objects

* Property names are now stored in camelCase in the database and the model JSON file, e.g. `dateCreated` for the
  attribute `date_created`, like in the other ObjectBox languages (Java, Kotlin, Dart, Swift). This makes it easy to
  share the model with them, e.g. for Sync, and shows the same names e.g. in the ObjectBox Admin.
  Python code is not affected: it still uses the attribute names.
  Existing databases and model JSON files are updated automatically: the properties are renamed, keeping their data.
  To store names as written in Python instead, use `@Entity(python_names=True)`.\
  **Breaking:** property names in the database and the model JSON file change (only for names with underscores);
  e.g. queries in the ObjectBox Admin or data in MongoDB (via Sync) use the new names.
* To-one relations: the new property type `Relation` stores the ID of an object of the target entity, e.g.
  `customer_id = Relation(Customer)` (or `Relation("Customer")`, e.g. to refer to the entity itself). Values are plain
  ints (0 for none); unlike an `Int64`, ObjectBox knows the target, e.g. removing the target object resets the relation
  to 0. It has an index (like the other ObjectBox languages, without zero values) and the usual integer conditions.
  An existing `Int64` property cannot be changed to a `Relation` (different type); add a new property instead.
* Box: new methods `contains(id)`, `get_many(ids)` and `update(object)`
  (the latter raises if the object does not exist yet, i.e. unlike `put()` it never inserts)
* Putting objects with `None` values: a property set to `None` is stored as null (left out of the stored object), where
  putting failed before. Reading is unchanged: a null value reads back as the property's default (e.g. `""`, `0`), as
  any property missing from a stored object. Properties that are not set at all are still stored with their default.
  Exceptions: `None` inside a vector or list still fails; `Flex` properties store `None` as a value (as before).
* Fix `Int8List` properties: putting and reading objects failed. Values are lists of signed 8-bit integers (-128 to 127).
* Fix reading list properties (e.g. `Int32List`) that are not present in a stored object, e.g. added to the entity
  after the object was put: this failed instead of returning an empty list.
* Fix reading `Date`/`DateNano` properties with `datetime` values, vector properties with numpy arrays (e.g. `Float32Vector`)
  and `Flex` properties that are not present in a stored object (e.g. added to the entity after the object was put):
  this failed with a `TypeError`. They read as the default now, like unset properties: the epoch (UTC), an empty array
  and `None`.

### Sync your data

* New module `objectbox.sync` with a Sync client (`Sync.client()`, `SyncClient`) to synchronize data
  with an ObjectBox Sync server (which stores your data centrally with optional sync to MongoDB)
* `@SyncEntity()` enables Sync for an entity (optionally with shared global IDs);
  `SyncClock` and `SyncPrecedence` properties for Sync conflict resolution.
* Client options include Sync filter variables, flags (`SyncFlags`) and certificate paths.
* Listeners for login, connection, completed, change and server time events.
* Requires the Sync variant of the C library: install the new package `objectbox-sync` instead of `objectbox`
  (`pip install objectbox-sync`; it installs `objectbox-api` and `objectbox-sync-clib`, the Sync variant of the library).

### Exceptions

* All exceptions raised by the database now derive from `DbError`, with a specific subclass per error,
  e.g. `IdNotFoundError`, `UniqueViolatedError` or `DbFullError` (see module `objectbox.exceptions`).
  `IllegalArgumentError` is also a `ValueError`, `IllegalStateError` and `FeatureNotAvailable` are also a
  `RuntimeError`, so they can be caught as the matching built-in exception, too.\
  **Breaking:** this replaces `CoreException` and `NotFoundException` (the latter was exported by the top-level module).

### Store

* Log callback (`log_callback` option): the log level values passed to the callback changed (see `LogLevel`, now also
  `Trace`); code comparing against `LogLevel` members is not affected.
* A store that is no longer referenced is now closed right away (was: only when Python's cyclic GC ran);
  e.g. on Windows, reopening the same directory could fail with "another store is still open using the same path".
  Still, prefer closing stores explicitly via `close()`.
* Fix the `model_bytes` and `model_bytes_direct` options (failed with a `TypeError`)
* Fix using a model JSON file with an empty `lastIndexId` (failed with a `ValueError`), e.g. one shared with
  an app using ObjectBox C++ or Go, which write it like this if there is no index

### Other

* API reference documentation (docstrings for the public API; generated via Sphinx)
* Example "tasks": added a command to remove tasks and improved the command line

4.0.0 (2024-05-28)
------------------

* ObjectBox now supports vector search ("vector database") to enable efficient similarity searches.
  This is particularly useful for AI/ML/RAG applications, e.g. image, audio, or text similarity.
  Other use cases include sematic search or recommendation engines.
  See https://docs.objectbox.io/ann-vector-search for details.
* The definition of entities (aka the data model) is now greatly simplified
  * Type-specific property classes, e.g. `name: String`, `count: Int64`, `score: Float32`
  * Automatic ID/UID and model management (i.e. add/remove/rename of entities and properties)
  * Automatic discovery of @Entity classes
* Queries: property-based conditions, e.g. `box.query(City.name.starts_with("Be"))`
* Queries: logical operators, e.g. `box.query(City.name == "Berlin" | City.name == "Munich")`
* Convenient "Store" API (deprecates ObjectBox and Builder API)
* New examples added, illustrating an VectorSearch and AI/RAG application
* Stable flat public API provided by single top-level module objectbox
* Dependency flatbuffers: Updated to 24.3.50
* Adjusting the version number to match the core version (4.0); we will be aligning on major versions from now on.

Older Versions
--------------
Please check https://github.com/objectbox/objectbox-python/releases for details.