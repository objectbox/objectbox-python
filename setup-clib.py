import setuptools
import os
import objectbox
with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="objectbox-clib",
    version=str(objectbox.version),
    author="ObjectBox",
    description="ObjectBox is a superfast lightweight database for objects (clib backend)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://objectbox.io",
    packages=setuptools.find_packages(
        include=['objectbox_clib']
    ),
    project_urls={
        'GitHub': 'https://github.com/objectbox/objectbox-python',
        'Tracker': 'https://github.com/objectbox/objectbox-python/issues',
    },
    python_requires='>=3.4, <4',
    license='ObjectBox Binary License v2.0-beta',
    license_files=["objectbox_clib/LICENSE"],
    package_data={
        'objectbox_clib': [
            # Linux, macOS
            'lib/x86_64/*',
            'lib/aarch64/*',
            'lib/armv7l/*',
            'lib/armv6l/*',
            'lib/macos-universal/*',
            # Windows
            'lib/AMD64/*',
        ],
    } 
)
