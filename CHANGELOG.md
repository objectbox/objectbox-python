ObjectBox Python ChangeLog
==========================

4.0.0 (2024-05-28)
------------------

* ObjectBox now supports vector search ("vector database") to enable efficient similarity searches.
  This is particularly useful for AI/ML/RAG applications, e.g. image, audio, or text similarity.
  Other use cases include sematic search or recommendation engines.
  See https://docs.objectbox.io/ann-vector-search for details.
* Queries: support for Property-based conditions and logic combinations 
* Convenient "Store" API deprecates ObjectBox and Builder API
* New examples added, illustrating an VectorSearch and AI/RAG application
* Dependency flatbuffers: Updated to 24.3.50
* Adjusting the version number to match the core version (4.0); we will be aligning on major versions from now on.

Older Versions
--------------
Please check https://github.com/objectbox/objectbox-python/releases for details.