# Builds the metapackage objectbox (no Python code), which users install: it depends on objectbox-api (the Python
# binding, setup.py) and objectbox-clib (the C library, setup-clib.py).
#   python setup-meta.py bdist_wheel           (run by `make build`)
# With --sync as the first argument, builds the metapackage objectbox-sync instead (`make build-sync`), which depends on
# objectbox-sync-clib (the Sync variant of the C library) instead of objectbox-clib. Sync users install objectbox-sync
# instead of objectbox (not in addition).
import os
import shutil
import sys

import setuptools

from build_info import binding_version, clib_version, AUTHOR, URL, PROJECT_URLS, PYTHON_REQUIRES, LICENSE, CLASSIFIERS

SYNC = sys.argv[1:2] == ["--sync"]
if SYNC:
    del sys.argv[1]  # Not an argument for setuptools

SYNC_LONG_DESCRIPTION = """ObjectBox Python with Sync
==========================
[ObjectBox](https://objectbox.io) is a superfast lightweight database for objects and vectors.
This package installs ObjectBox Python with [ObjectBox Sync](https://objectbox.io/sync/) support:
the Python API (package `objectbox-api`) and the Sync variant of the ObjectBox C library (package `objectbox-sync-clib`).

Install it instead of the [objectbox](https://pypi.org/project/objectbox/) package (not in addition):
```bash
pip install objectbox-sync
```

The Python API is the same as for `objectbox` (import package `objectbox`); see
[objectbox](https://pypi.org/project/objectbox/) and [objectbox-python](https://github.com/objectbox/objectbox-python)
for documentation.
"""


def setup():
    if SYNC:
        name = "objectbox-sync"
        description = "ObjectBox is a superfast lightweight database for objects, with Sync"
        long_description = SYNC_LONG_DESCRIPTION
        clib = "objectbox-sync-clib"
    else:
        name = "objectbox"
        description = "ObjectBox is a superfast lightweight database for objects"
        with open("README.md", "r") as fh:  # The main PyPI page
            long_description = fh.read()
        clib = "objectbox-clib"

    setuptools.setup(
        name=name,
        version=binding_version(),
        author=AUTHOR,
        description=description,
        long_description=long_description,
        long_description_content_type="text/markdown",
        url=URL,
        project_urls=PROJECT_URLS,
        python_requires=PYTHON_REQUIRES,
        license=LICENSE,
        classifiers=CLASSIFIERS,
        install_requires=[
            # The Python binding of exactly this version
            'objectbox-api==' + binding_version(),
            # The binding requires an exact C library version (checked at runtime); the ".*" allows post-releases
            # of the library package, e.g. 4.0.0.post1 to fix packaging issues.
            clib + '==' + clib_version() + '.*',
        ],
        packages=[],  # Metapackage: no Python code (explicitly empty, otherwise setuptools discovers packages)
    )


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.realpath(__file__)))
    # Remove build output of other packages (e.g. build/lib/objectbox from setup.py); bdist_wheel would include it
    shutil.rmtree("build", ignore_errors=True)
    setup()
    shutil.rmtree("build", ignore_errors=True)
