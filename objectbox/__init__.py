from objectbox.box import Box
from objectbox.builder import Builder
from objectbox.model import Model
from objectbox.objectbox import ObjectBox
from objectbox.c import NotFoundException, version_core
from objectbox.version import Version

__all__ = [
    'Box',
    'Builder',
    'Model',
    'ObjectBox',
    'NotFoundException',
    'version',
    'version_info',
]

# Python binding version
version = Version(0, 1, 0)


def version_info():
    return "ObjectBox Python version " + str(version) + " using dynamic library version " + str(version_core)
