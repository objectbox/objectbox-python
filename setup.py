import setuptools

from build_info import binding_version, clib_version

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="objectbox",
    version=binding_version(),
    author="ObjectBox",
    description="ObjectBox is a superfast lightweight database for objects",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://objectbox.io",
    project_urls={
        'GitHub': 'https://github.com/objectbox/objectbox-python',
        'Tracker': 'https://github.com/objectbox/objectbox-python/issues',
    },
    python_requires='>=3.4, <4',
    license='Apache 2.0',
    classifiers=[
        "Development Status :: 5 - Production/Stable"

        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: C",
        "Programming Language :: C++",

        'Operating System :: POSIX :: Linux',
        'Operating System :: MacOS',
        'Operating System :: Microsoft :: Windows',

        "Topic :: Database",
        "Topic :: Database :: Database Engines/Servers",
        "Topic :: Database :: Front-Ends",
        "Topic :: Software Development",
        "Topic :: Software Development :: Libraries",

        "License :: OSI Approved :: Apache Software License",
        "Intended Audience :: Developers",
    ],

    install_requires=[
       # The binding requires an exact C library version (checked at runtime); the ".*" allows post-releases
       # of objectbox-clib, e.g. 4.0.0.post1 to fix packaging issues.
       'objectbox-clib==' + clib_version() + '.*',
       # A range instead of an exact pin, so we do not force a specific version on users that also depend on
       # flatbuffers via other packages. The lower bound is the previously pinned version known to work; no upper bound as
       # flatbuffers uses date-based versions (no semver), so its "major" version does not indicate breaking changes.
       'flatbuffers>=24.3.25',
       'numpy'
    ],

    packages=setuptools.find_packages(exclude=['exampl*', 'objectbox_clib*']), 
)
