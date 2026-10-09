import os

import pytest

import objectbox.c as c

try:
    from importlib import metadata
except ImportError:  # Python 3.7
    metadata = None


def installed_clib_distribution():
    """The installed distribution of the C library package in use (objectbox-clib or objectbox-sync-clib),
    if the package is used from it (i.e. not from the source tree)."""
    if metadata is None:
        pytest.skip("importlib.metadata requires Python 3.8+")
    package_name = c.clib_package.__name__  # objectbox_clib or objectbox_sync_clib
    imported_init = os.path.realpath(c.clib_package.__file__)
    # Note: there may be several (e.g. build metadata in the source tree); find the one the package is imported from
    for distribution in metadata.distributions():
        if distribution.metadata["Name"] == package_name.replace("_", "-") and distribution.read_text("WHEEL") is not None:
            if os.path.realpath(str(distribution.locate_file(package_name + "/__init__.py"))) == imported_init:
                return distribution
    pytest.skip(package_name + " is not used from an installed wheel (e.g. running from source)")


def test_clib_platform_wheel():
    """The installed C library package must be a platform wheel, containing only the library that is actually loaded."""
    distribution = installed_clib_distribution()

    tags = [line.split(":", 1)[1].strip() for line in distribution.read_text("WHEEL").splitlines()
            if line.startswith("Tag:")]
    assert len(tags) == 1
    assert not tags[0].endswith("-any"), "Expected a platform specific wheel (see setup-clib.py)"

    package_dir = os.path.dirname(os.path.realpath(c.clib_package.__file__))
    lib_dir = os.path.dirname(os.path.realpath(c.lib_path))
    assert os.path.dirname(lib_dir) == os.path.join(package_dir, "lib"), "Library not loaded from the C library package"
    assert os.listdir(os.path.join(package_dir, "lib")) == [os.path.basename(lib_dir)], \
        "Only the library for this platform shall be installed"


@pytest.mark.parametrize("system, machine, maxsize, sys_platform, expected", [
    ("Linux", "x86_64", 2 ** 63 - 1, "linux-x86_64", "x86_64"),
    ("Linux", "aarch64", 2 ** 63 - 1, "linux-aarch64", "aarch64"),
    ("Linux", "aarch64", 2 ** 31 - 1, "linux-aarch64", "armv7l"),  # 32-bit Python on a 64-bit kernel (e.g. Raspberry Pi OS 32-bit)
    ("Linux", "armv7l", 2 ** 31 - 1, "linux-armv7l", "armv7l"),
    ("Windows", "AMD64", 2 ** 63 - 1, "win-amd64", "AMD64"),
    ("Windows", "ARM64", 2 ** 63 - 1, "win-arm64", "ARM64"),
    ("Windows", "ARM64", 2 ** 63 - 1, "win-amd64", "AMD64"),  # x64 Python (emulated) on Windows ARM64
    ("Darwin", "arm64", 2 ** 63 - 1, "macosx-11.0-arm64", "macos-universal"),
    ("Darwin", "x86_64", 2 ** 63 - 1, "macosx-11.0-x86_64", "macos-universal"),
])
def test_lib_dir_name(monkeypatch, system, machine, maxsize, sys_platform, expected):
    monkeypatch.setattr(c.platform, "system", lambda: system)
    monkeypatch.setattr(c.platform, "machine", lambda: machine)
    monkeypatch.setattr(c.sys, "maxsize", maxsize)
    monkeypatch.setattr(c.sysconfig, "get_platform", lambda: sys_platform)
    assert c.lib_dir_name() == expected
