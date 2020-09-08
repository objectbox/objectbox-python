Contributing
------------------
Anyone can contribute, be it by coding, improving docs or just proposing a new feature. 
As a new contributor, you may want to have a look at some of the following issues:
* [**good first issue**](https://github.com/objectbox/objectbox-python/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22) tag 
* [**help wanted**](https://github.com/objectbox/objectbox-python/issues?q=is%3Aissue+is%3Aopen+label%3A%22help+wanted%22) tag

When picking up an existing issue, please let others know in the issue comment. 
Don't hesitate to reach out for guidance or to discuss a solution proposal!

### Code contributions
When creating a Pull Request for code changes, please check that you cover the following:
* Include tests for the changes you introduce. See the [tests folder](tests) for examples.
* Formatted the code according to PEP-8

### Basic technical approach
ObjectBox offers a [C API](https://github.com/objectbox/objectbox-c) which can be integrated into python using
[ctypes](https://docs.python.org/dev/library/ctypes.html).
The C API is is also used by the ObjectBox language bindings for [Go](https://github.com/objectbox/objectbox-go), 
[Swift](https://github.com/objectbox/objectbox-swift), and [Dart/Flutter](https://github.com/objectbox/objectbox-dart).
These language bindings currently serve as an example for this Python implementation.
Internally, ObjectBox uses [FlatBuffers](https://google.github.io/flatbuffers/) to store objects.

The main prerequisite to using the Python APIs is the ObjectBox binary library (.so, .dylib, .dll depending on your 
platform) which actually implements the database functionality. The library should be placed in the 
`objectbox/lib/[architecture]/` folder of the checked out repository. You can get/update it by running `make get-lib`.

### Getting started as a contributor
#### Initial setup
If you're just getting started, run the following simple steps to set up the repository on your machine
* clone this repository
* `pip install virtualenv` install [virtualenv](https://pypi.org/project/virtualenv/) if you don't have it yet
* `make init` initialize the virtualenv
* `make get-lib` get the objectbox-c shared library for your platform; also run this to update to a newer version

#### Regular development workflow
You'll probably use the following commands regularly when implementing a new feature in the library:
* `make test` to make sure everything works as expected after your changes
* `make benchmark` to measure the CRUD performance on your machine - if you're working on a performance-related change
