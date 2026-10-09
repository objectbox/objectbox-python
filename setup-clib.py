# Builds the objectbox-clib package containing the ObjectBox C library (no Python code).
# There is one wheel per platform, tagged for the platform, so pip installs only the library for the user's platform:
#   python setup-clib.py bdist_wheel --plat-name <platform tag>   (one of PLATFORMS below)
#   python setup-clib.py all                                      (all platforms, run by `make build`)
# There is no wheel for other platforms (e.g. no "any" wheel with all libraries); pip fails to install there.
import os
import shutil
import subprocess
import sys

import setuptools

try:
    from setuptools.command.bdist_wheel import bdist_wheel  # setuptools 70.1+
except ImportError:
    from wheel.bdist_wheel import bdist_wheel

from build_info import clib_version

# Wheel platform tag -> library directory (inside objectbox_clib/lib) for that platform.
# The tags express the minimum OS requirements of the libraries:
# - Linux: glibc 2.28 (as documented for objectbox-c); manylinux tags are required for PyPI.
# - macOS: 11.0 (the library's minimum version); since macOS 11, pip only considers major versions for wheel tags.
# Linux armv6l (e.g. Raspberry Pi Zero) is not supported: pip does not support manylinux for armv6l and PyPI does not
# accept plain "linux_armv6l" wheels.
PLATFORMS = {
    "manylinux_2_28_x86_64": "x86_64",
    "manylinux_2_28_aarch64": "aarch64",
    "manylinux_2_28_armv7l": "armv7l",
    "macosx_11_0_universal2": "macos-universal",
    "win_amd64": "AMD64",
}


def build_all():
    for tag in PLATFORMS:
        # Remove build output from the previous platform; otherwise its library would end up in the next wheel too
        shutil.rmtree("build", ignore_errors=True)
        subprocess.check_call([sys.executable, __file__, "bdist_wheel", "--plat-name", tag])
    shutil.rmtree("build", ignore_errors=True)


def platform_tag_from_args():
    for i, arg in enumerate(sys.argv):
        if arg == "--plat-name" and i + 1 < len(sys.argv):
            return sys.argv[i + 1]
        if arg.startswith("--plat-name="):
            return arg.split("=", 1)[1]
    return None


class BinaryDistribution(setuptools.Distribution):
    """Marks the package as platform specific (contains a native library), which is not detected automatically."""

    def has_ext_modules(self):
        return True


class PlatformWheel(bdist_wheel):
    """Tags the wheel for the given platform but for any Python 3 version (the library does not use the Python API)."""

    def get_tag(self):
        return "py3", "none", self.plat_name


def setup():
    platform_tag = platform_tag_from_args()
    if platform_tag not in PLATFORMS:
        raise ValueError(f"Missing or unsupported --plat-name: {platform_tag}; supported: {', '.join(PLATFORMS)}")

    with open("objectbox_clib/README.md", "r") as fh:  # Not the main README (e.g. license differs)
        long_description = fh.read()

    setuptools.setup(
        name="objectbox-clib",
        version=clib_version(),
        author="ObjectBox",
        description="ObjectBox C library (native binary) for the objectbox Python package",
        long_description=long_description,
        long_description_content_type="text/markdown",
        url="https://objectbox.io",
        packages=setuptools.find_packages(
            include=['objectbox_clib']
        ),
        project_urls={
            'GitHub': 'https://github.com/objectbox/objectbox-python',
            'Tracker': 'https://github.com/objectbox/objectbox-python/issues',
            'Changelog': 'https://github.com/objectbox/objectbox-c/blob/main/CHANGELOG.md',  # Version of the C library
            'License': 'https://objectbox.io/0209-ob-binary-license/',
        },
        python_requires='>=3.4, <4',
        license='ObjectBox Binary License (https://objectbox.io/0209-ob-binary-license/)',
        license_files=["objectbox_clib/LICENSE"],
        package_data={
            'objectbox_clib': ['lib/' + PLATFORMS[platform_tag] + '/*'],
        },
        cmdclass={'bdist_wheel': PlatformWheel},
        distclass=BinaryDistribution,
    )


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.realpath(__file__)))
    if sys.argv[1:] == ["all"]:
        build_all()
    else:
        setup()
