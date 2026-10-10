# Builds the objectbox-api package: the Python binding (import package "objectbox"), without the C library.
# Users install one of the metapackages instead (setup-meta.py), which add the C library package:
# objectbox (with objectbox-clib) or objectbox-sync (with objectbox-sync-clib).
import setuptools

from build_info import binding_version, AUTHOR, URL, PROJECT_URLS, PYTHON_REQUIRES, LICENSE, CLASSIFIERS

long_description = """ObjectBox Python API
====================
This package contains the Python API of [ObjectBox](https://objectbox.io), a superfast lightweight database for
objects and vectors (import package `objectbox`), but not the ObjectBox C library it requires.

You do not need to install this package directly: install [objectbox](https://pypi.org/project/objectbox/) instead,
or [objectbox-sync](https://pypi.org/project/objectbox-sync/) for [ObjectBox Sync](https://objectbox.io/sync/).
Both depend on this package and add the matching C library.
```bash
pip install objectbox
```

See [objectbox](https://pypi.org/project/objectbox/) and
[objectbox-python](https://github.com/objectbox/objectbox-python) for documentation.
"""

setuptools.setup(
    name="objectbox-api",
    version=binding_version(),
    author=AUTHOR,
    description="ObjectBox Python API (without the C library; install objectbox or objectbox-sync)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url=URL,
    project_urls=PROJECT_URLS,
    python_requires=PYTHON_REQUIRES,
    license=LICENSE,
    classifiers=CLASSIFIERS,

    # No C library dependency: the metapackages objectbox and objectbox-sync add objectbox-clib or objectbox-sync-clib
    install_requires=[
       # A range instead of an exact pin, so we do not force a specific version on users that also depend on
       # flatbuffers via other packages. The lower bound is the previously pinned version known to work; no upper bound as
       # flatbuffers uses date-based versions (no semver), so its "major" version does not indicate breaking changes.
       'flatbuffers>=24.3.25',
       'numpy'
    ],

    packages=setuptools.find_packages(exclude=['exampl*', 'objectbox_clib*', 'objectbox_sync_clib*']),
)
