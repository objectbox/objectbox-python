import setuptools
import objectbox

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="objectbox",
    version=str(objectbox.version),
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
        "Development Status :: 3 - Alpha",

        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
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
       'flatbuffers==23.5.26',
    ],

    packages=setuptools.find_packages(),
    package_data={
        'objectbox': [
            # Linux, macOS
            'lib/x86_64/*',
            'lib/armv7l/*',
            'lib/armv6l/*',
            # Windows
            'lib/AMD64/*',
        ],
    }
)
