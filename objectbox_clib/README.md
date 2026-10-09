ObjectBox C library for Python
==============================
This package contains the pre-built native [ObjectBox](https://objectbox.io) library (C library) used by the
[objectbox](https://pypi.org/project/objectbox/) Python package. It contains no Python API.

You do not need to install this package directly: install `objectbox` instead, which depends on this package.
```bash
pip install objectbox
```

There is a wheel for each supported platform, so only the library for your platform is installed:
Linux x86_64, aarch64 and armv7l (glibc 2.28+), macOS 13+ (Intel and Apple Silicon) and Windows x64.

The version of this package is the version of the ObjectBox C library it contains.

License
-------
The pre-built native library contained in this package is licensed under the
[ObjectBox Binary Licence Agreement](https://objectbox.io/0209-ob-binary-license/).

The ObjectBox Python binding (package `objectbox`) is licensed separately under the Apache License 2.0;
see [objectbox-python](https://github.com/objectbox/objectbox-python).
