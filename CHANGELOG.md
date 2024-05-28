ObjectBox Python ChangeLog
==========================

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