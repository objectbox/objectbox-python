import os
import sys
import types

import pytest

import objectbox

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


def installed_distribution_of(package, top_level_name: str):
    """The installed distribution (wheel) the given package is imported from, or None (e.g. from the source tree)."""
    init_file = top_level_name + "/__init__.py"
    imported_init = os.path.realpath(package.__file__)
    for distribution in metadata.distributions():
        # Note: locate_file() resolves any path relative to the distribution's location; check the file is its own
        if distribution.read_text("WHEEL") is not None and init_file in [str(f) for f in distribution.files or []]:
            if os.path.realpath(str(distribution.locate_file(init_file))) == imported_init:
                return distribution
    return None


def test_api_and_metapackage():
    """The Python code comes from objectbox-api, and a metapackage (objectbox or objectbox-sync) ties it to the C library
    package in use (installed wheels only)."""
    if metadata is None:
        pytest.skip("importlib.metadata requires Python 3.8+")
    api_distribution = installed_distribution_of(objectbox, "objectbox")
    if api_distribution is None:
        pytest.skip("objectbox is not used from an installed wheel (e.g. running from source)")
    assert api_distribution.metadata["Name"] == "objectbox-api"
    assert api_distribution.version == str(objectbox.version)
    assert not [r for r in (api_distribution.requires or []) if "clib" in r], "objectbox-api must not depend on a C library"

    clib_distribution = installed_clib_distribution()
    clib_name = clib_distribution.metadata["Name"]  # objectbox-clib or objectbox-sync-clib
    meta_name = {"objectbox-clib": "objectbox", "objectbox-sync-clib": "objectbox-sync"}[clib_name]
    meta_distribution = metadata.distribution(meta_name)
    requires = meta_distribution.requires
    assert "objectbox-api==" + str(objectbox.version) in requires
    assert clib_name + "==" + c.required_version + ".*" in requires
    assert meta_distribution.files is None or not [f for f in meta_distribution.files if f.suffix == ".py"], \
        "Metapackage must not contain code"


def fake_clib_package(tmp_path, name: str, with_lib: bool = True) -> types.ModuleType:
    """A fake C library package (module) in tmp_path, with an (empty) library file for this platform if with_lib."""
    package_dir = tmp_path / name
    package_dir.mkdir()
    (package_dir / "__init__.py").write_text("")
    if with_lib:
        lib_dir = package_dir / "lib" / c.lib_dir_name()
        lib_dir.mkdir(parents=True)
        (lib_dir / c.shlib_name("objectbox")).write_text("")
    module = types.ModuleType(name)
    module.__file__ = str(package_dir / "__init__.py")
    return module


@pytest.mark.parametrize("sync, sync_lib, standard, expected", [
    (True, True, True, "objectbox_sync_clib"),  # Both metapackages installed: Sync preferred
    (True, True, False, "objectbox_sync_clib"),  # objectbox-sync only
    (False, False, True, "objectbox_clib"),  # objectbox only
    (True, False, True, "objectbox_clib"),  # Sync package without library for the platform (e.g. source tree)
    (False, False, False, None),  # Neither (e.g. objectbox-api alone)
    (True, False, False, None),
])
def test_lib_package(monkeypatch, tmp_path, sync, sync_lib, standard, expected):
    # A None entry in sys.modules makes the import fail with ImportError
    monkeypatch.setitem(sys.modules, "objectbox_sync_clib",
                        fake_clib_package(tmp_path, "objectbox_sync_clib", sync_lib) if sync else None)
    monkeypatch.setitem(sys.modules, "objectbox_clib",
                        fake_clib_package(tmp_path, "objectbox_clib") if standard else None)
    if expected is None:
        with pytest.raises(ImportError, match="pip install objectbox-sync"):
            c.lib_package()
    else:
        assert c.lib_package().__name__ == expected


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
