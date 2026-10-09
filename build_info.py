# Versions for building/packaging, read from the sources (single source of truth).
# Note: the objectbox package is not imported, as this would load the C library (not needed or available for a build).

import ast
import importlib.util
import os
import re

_root_dir = os.path.dirname(os.path.realpath(__file__))


def _read(rel_path: str) -> str:
    with open(os.path.join(_root_dir, rel_path), "r") as file:
        return file.read()


def _find_in_file(rel_path: str, pattern: str) -> re.Match:
    match = re.search(pattern, _read(rel_path), re.MULTILINE)
    if not match:
        raise ValueError(f"Pattern {pattern} not found in {rel_path}")
    return match


def binding_version() -> str:
    """Version of the objectbox (Python binding) package, e.g. "5.0.0" or "5.0.0b1".
    Evaluates the arguments of "version = Version(...)" in objectbox/__init__.py (literals only) and formats them
    using the Version class (objectbox/version.py, which has no dependencies; loaded directly, not via the package)."""
    for node in ast.parse(_read("objectbox/__init__.py")).body:
        if (isinstance(node, ast.Assign) and [getattr(t, "id", None) for t in node.targets] == ["version"]
                and isinstance(node.value, ast.Call) and getattr(node.value.func, "id", None) == "Version"):
            args = [ast.literal_eval(arg) for arg in node.value.args]
            kwargs = {kw.arg: ast.literal_eval(kw.value) for kw in node.value.keywords}
            spec = importlib.util.spec_from_file_location("_objectbox_version", os.path.join(_root_dir, "objectbox/version.py"))
            version_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(version_module)
            return str(version_module.Version(*args, **kwargs))
    raise ValueError("version = Version(...) not found in objectbox/__init__.py")


def clib_version() -> str:
    """Version of the ObjectBox C library required by the binding; also the version of the objectbox-clib package."""
    return _find_in_file("objectbox/c.py", r'^required_version = "([^"]+)"').group(1)
