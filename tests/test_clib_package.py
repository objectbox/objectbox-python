import os

import pytest

import objectbox.c as c
import objectbox_clib

try:
    from importlib import metadata
except ImportError:  # Python 3.7
    metadata = None


def installed_clib_distribution():
    """The installed objectbox-clib distribution, if objectbox_clib is used from it (i.e. not from the source tree)."""
    if metadata is None:
        pytest.skip("importlib.metadata requires Python 3.8+")
    imported_init = os.path.realpath(objectbox_clib.__file__)
    # Note: there may be several (e.g. build metadata in the source tree); find the one objectbox_clib is imported from
    for distribution in metadata.distributions():
        if distribution.metadata["Name"] == "objectbox-clib" and distribution.read_text("WHEEL") is not None:
            if os.path.realpath(str(distribution.locate_file("objectbox_clib/__init__.py"))) == imported_init:
                return distribution
    pytest.skip("objectbox_clib is not used from an installed objectbox-clib wheel (e.g. running from source)")


def test_clib_platform_wheel():
    """The installed objectbox-clib must be a platform wheel, containing only the library that is actually loaded."""
    distribution = installed_clib_distribution()

    tags = [line.split(":", 1)[1].strip() for line in distribution.read_text("WHEEL").splitlines()
            if line.startswith("Tag:")]
    assert len(tags) == 1
    assert not tags[0].endswith("-any"), "Expected a platform specific wheel (see setup-clib.py)"

    package_dir = os.path.dirname(os.path.realpath(objectbox_clib.__file__))
    lib_dir = os.path.dirname(os.path.realpath(c.lib_path))
    assert os.path.dirname(lib_dir) == os.path.join(package_dir, "lib"), "Library not loaded from objectbox-clib"
    assert os.listdir(os.path.join(package_dir, "lib")) == [os.path.basename(lib_dir)], \
        "Only the library for this platform shall be installed"


@pytest.mark.parametrize("system, machine, maxsize, expected", [
    ("Linux", "x86_64", 2 ** 63 - 1, "x86_64"),
    ("Linux", "aarch64", 2 ** 63 - 1, "aarch64"),
    ("Linux", "aarch64", 2 ** 31 - 1, "armv7l"),  # 32-bit Python on a 64-bit kernel (e.g. Raspberry Pi OS 32-bit)
    ("Linux", "armv7l", 2 ** 31 - 1, "armv7l"),
    ("Windows", "AMD64", 2 ** 63 - 1, "AMD64"),
    ("Darwin", "arm64", 2 ** 63 - 1, "macos-universal"),
    ("Darwin", "x86_64", 2 ** 63 - 1, "macos-universal"),
])
def test_lib_dir_name(monkeypatch, system, machine, maxsize, expected):
    monkeypatch.setattr(c.platform, "system", lambda: system)
    monkeypatch.setattr(c.platform, "machine", lambda: machine)
    monkeypatch.setattr(c.sys, "maxsize", maxsize)
    assert c.lib_dir_name() == expected
