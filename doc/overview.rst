API Overview
============

This gives an overview of the ObjectBox Python API by showing most important parts to get started.

For beginners, we recommend our `Python database docs <https://docs.objectbox.io/>`_ at for more details;
especially the `Getting Started <https://docs.objectbox.io/getting-started>`_ guide.
This covers more than just the obligatory ``pip install --upgrade objectbox``.
    
    .. currentmodule:: objectbox

Defining the Data Model
-----------------------

The ``@Entity`` decorator is used to define a class as an ObjectBox entity.

  .. autosummary:: 
        :nosignatures:

        Entity

Each entity class defines a set of properties. The following property types are most commonly used:

  .. autosummary:: 
        :nosignatures:

        Id
        String
        Int32
        Int64
        Float32
        Float64
        Date
        Float32Vector

Note: ``Float32Vector`` is used for `on-device vector search <https://docs.objectbox.io/on-device-vector-search>`_.

Classes
-------

Now, with the data model defined, you can start using the ObjectBox database.
These are the main classes to interact with:

    .. autosummary::
        :nosignatures:
        
        Store
        Box
        QueryBuilder
        Query

What's next
-----------

* `Python database docs (docs.objectbox.io) <https://docs.objectbox.io/>`_
* API reference (next in this API documentation)
