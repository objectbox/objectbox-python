ObjectBox Python ChangeLog
==========================

5.0.0b1 (unreleased)
--------------------

* Update to ObjectBox C library 5.3.2 (was 4.0.0), see https://github.com/objectbox/objectbox-c/blob/main/CHANGELOG.md;
* New platform: Windows ARM64 (64-bit ARM, e.g. Snapdragon-based devices)
* Log callback (`log_callback`): the log level values passed to the callback changed (see `LogLevel`, now also `Trace`);
  code comparing against `LogLevel` members is not affected.
* The ObjectBox C library is now a separate package, `objectbox-clib`, which is installed automatically as a dependency.
  There is a wheel for each platform, so only the library for your platform is downloaded (was: libraries for all platforms):
  Linux x86_64, aarch64 and armv7l (glibc 2.28+), macOS 11+ (universal) and Windows x64 and ARM64 (new).
  **Breaking:** Linux ARMv6hf (e.g. Raspberry Pi Zero/1) is no longer supported, as PyPI does not support wheels for it.
* Linux: support 32-bit Python on a 64-bit kernel, e.g. Raspberry Pi OS 32-bit on a Raspberry Pi 4/5
  (64-bit kernel by default); this failed to load the library before.
* Box: new methods `contains(id)`, `get_many(ids)` and `update(object)`
  (the latter raises if the object does not exist yet, i.e. unlike `put()` it never inserts)
* Exceptions: all exceptions raised by the database now derive from `DbError`, with a specific subclass per error,
  e.g. `IdNotFoundError`, `UniqueViolatedError` or `DbFullError` (see module `objectbox.exceptions`).
  **Breaking:** this replaces `CoreException` and `NotFoundException` (the latter was exported by the top-level module).
* Store: new `log_callback` option to receive the database's log messages
* Top-level module now also exports `Query`, `QueryBuilder`, `PropertyQueryCondition` and `HnswFlags`
* API reference documentation (docstrings for the public API; generated via Sphinx)
* Example "tasks": added a command to remove tasks and improved the command line
* Dependency flatbuffers: any version from 24.3.25 on is accepted now (was pinned to 24.3.25); tested up to 25.12.19
* Store: a store that is no longer referenced is now closed right away (was: only when Python's cyclic GC ran);
  e.g. on Windows, reopening the same directory could fail with "another store is still open using the same path".
  Still, prefer closing stores explicitly via `close()`.
* Store: fix the `model_bytes` and `model_bytes_direct` options (failed with a `TypeError`)
* Store: faster opening of many stores, e.g. one store per user or agent. A model is synced with the model JSON file
  only once per process (also when given by name, e.g. the default model), saving about 0.1 ms per open.
  The new option `skip_model_sync` additionally opens existing stores with the schema stored in their database
  instead of checking it against the model, which halves the time to open (see its documentation for when to use it).
* Faster import: `import objectbox` no longer imports numpy (also not via flatbuffers, which imports numpy) and takes
  about half the time. numpy is imported when needed, e.g. for vector properties or the first put or get.
  Importing numpy may start BLAS threads (OpenBLAS: one per CPU core) that busy-wait for ~0.1 s, slowing down
  short-lived processes. With the experimental FlatBuffers codegen (see below), entities without vector or flex
  properties never import numpy or flatbuffers.
* Experimental: a fast FlatBuffers builder for putting objects, enabled via
  `objectbox.experimental.enable_fast_flatbuffers_builder()` (off by default). It produces the same bytes as before,
  with the layout precomputed per entity instead of using the generic `flatbuffers.Builder`; marshalling an object
  with a string and two numbers gets ~12x faster, putting 10,000 objects of the test entity ~4x faster.
* Experimental: FlatBuffers codegen for putting objects, enabled via `objectbox.experimental.enable_flatbuffers_codegen()`
  (off by default; replaces the fast builder if that is enabled). Like the fast builder, but generates Python code per
  entity at its first put, which is again ~2x faster for small objects (~25x faster than the generic builder);
  putting 10,000 objects of the test entity ~5x faster than the generic builder.
  Codegen also reads objects (get, queries) with generated code, returning the same objects: ~3.5x faster per object
  for a small entity, ~8x faster for 21 properties.

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