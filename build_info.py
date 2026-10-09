# Versions for building/packaging, read from the sources (single source of truth).
# Note: the objectbox package is not imported, as this would load the C library (not needed or available for a build).

import os
import re

_root_dir = os.path.dirname(os.path.realpath(__file__))


def _find_in_file(rel_path: str, pattern: str) -> re.Match:
    with open(os.path.join(_root_dir, rel_path), "r") as file:
        match = re.search(pattern, file.read(), re.MULTILINE)
    if not match:
        raise ValueError(f"Pattern {pattern} not found in {rel_path}")
    return match


def binding_version() -> str:
    """Version of the objectbox (Python binding) package, e.g. "4.0.0"."""
    match = _find_in_file("objectbox/__init__.py", r"^version = Version\((\d+), (\d+), (\d+)\)")
    return ".".join(match.groups())


def clib_version() -> str:
    """Version of the ObjectBox C library required by the binding; also the version of the objectbox-clib package."""
    return _find_in_file("objectbox/c.py", r'^required_version = "([^"]+)"').group(1)
