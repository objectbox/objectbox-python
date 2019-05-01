import ctypes
from objectbox.c import C


class Version:
    def __init__(self, major: int, minor: int, patch: int, label: str = ""):
        self.major = major
        self.minor = minor
        self.patch = patch
        self.label = label

    def __str__(self):
        result = ".".join(map(str, [self.major, self.minor, self.patch]))
        if len(self.label) > 0:
            result += "-" + self.label
        return result


# Python binding version
version_python = Version(0, 0, 0, "dev")

# load the core library version
__major = ctypes.c_int(0)
__minor = ctypes.c_int(0)
__patch = ctypes.c_int(0)
C.obx_version(ctypes.byref(__major), ctypes.byref(__minor), ctypes.byref(__patch))

# C-api (core library) version
version_library = Version(__major.value, __minor.value, __patch.value)


def version_info():
    return "ObjectBox Python version " + str(version_python) + " using dynamic library version " + str(version_library)
