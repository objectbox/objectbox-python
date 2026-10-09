# AGENTS.md

This file provides guidance to AI coding agents when working with code in this repository.

## Commands

All `make` targets use (and create if needed) the virtualenv in `.venv` from `requirements.txt`.

- `make depend` — set up venv and download the ObjectBox C shared libraries (`download-c-lib.py`) into `objectbox_clib/lib/<arch>/`. Required once after checkout and whenever the C library version changes.
- `make test` — run all tests (`python -m pytest --capture=no --verbose`)
- `make build` — clean and build the wheels into `dist/`: `objectbox` and `objectbox-clib` (one per platform plus a fallback)
- `make benchmark` — CRUD benchmark (`benchmark.py`)
- Single test: `.venv/bin/python -m pytest tests/test_query.py::test_name -s -v` (the venv gets pytest etc. from `requirements.txt` via any `make` target, e.g. `make depend`)

Run pytest from the repository root: tests import both `common` (via `tests/conftest.py`) and `tests.model`.

There is no linter configured; CONTRIBUTING.md asks for PEP-8 formatting.

## Architecture

Python binding for the ObjectBox C API (objectbox-c) via `ctypes`; objects are serialized with FlatBuffers.

- **`objectbox/c.py`** — all C bindings. Loads the library from the `objectbox_clib` package (`objectbox_clib/lib/<platform.machine()>/`, or `macos-universal`) at import and asserts the core version equals `required_version`. `required_version` is the single source of the C library version (see Packaging). Functions are declared with helpers: `c_fn` (checks result/pointer), `c_fn_rc` (returns `obx_err`, raises via `check_obx_err`), `c_fn_qb_cond`, `c_fn_nocheck`.
- **`objectbox/exceptions.py`** — `DbError` base class plus one subclass per `DbErrorCode`; `create_db_error(code)` maps C error codes to exception classes (message taken from `obx_last_error_message()`).
- **Model definition** (`objectbox/model/`):
  - `@Entity()` (`entity.py`) wraps a user class into an `_Entity` (handles FlatBuffers `_marshal`/`_unmarshal`) and registers it in the global `obx_models_by_name` under a model name (default `"default"`). Property classes used as bare class members (e.g. `name = String`) are instantiated by the decorator.
  - `properties.py` — typed `Property` classes (scalars, vectors/lists, Date, Flex, `HnswIndex` for vector search). Property operators/methods (`==`, `starts_with`, `nearest_neighbor`, …) produce `PropertyQueryCondition`s.
  - `idsync.py` — assigns IDs/UIDs by syncing the model against an `objectbox-model.json` file (read, matched by UID then name, rewritten from scratch). This is how renames/removals are tracked across schema changes.
- **`Store`** (`store.py`) — opening a store: resolve the model (a `Model` or a model name string → collect registered entities), locate `objectbox-model.json` (explicit `model_json_file`, else the calling module's directory found via the call stack, else `__main__`'s directory, else CWD), run `sync_model`, then build `StoreOptions` and call `obx_store_open`. Directory prefix `memory:` opens an in-memory DB.
- **`Box`** (`box.py`) — CRUD per entity. `box.query(condition)` returns a `QueryBuilder`; conditions (`condition.py`, combinable with `&`/`|`) are applied onto the C query builder, then `.build()` yields a `Query`.
- **Deprecated API**: `ObjectBox` and `Builder` are thin wrappers around `Store` kept for backward compatibility (`tests/test_deprecated.py`).
- Public API is the flat export list in `objectbox/__init__.py`; the binding version (`version = Version(...)`) is also defined there and used by `setup.py`.

## Packaging

Two pip packages are built from this repository:
- `objectbox` (`setup.py`): the Python binding; depends on the matching `objectbox-clib` version (`==<C version>.*`).
- `objectbox-clib` (`setup-clib.py`, package `objectbox_clib/`): only the C libraries, no Python code. Built as one wheel per platform (wheel platform tags in `PLATFORMS`, so pip picks the platform's library) plus a fallback wheel with all libraries (e.g. for Linux armv6l, which cannot be served by platform wheels on PyPI). Versioned like the C library.

`build_info.py` reads the binding version (`objectbox/__init__.py`) and the C library version (`required_version` in `objectbox/c.py`) as text for the build scripts and `download-c-lib.py`. Build scripts must not import `objectbox`: that loads the C library. To bump the C library, only change `required_version`, run `make depend`, and re-check the platform tags in `setup-clib.py` against the new libraries' minimum glibc/macOS versions.

## Tests

- `tests/model.py` defines test entities; `tests/common.py` has `create_test_store()` which deletes the DB dir (`testdata` by default) and `tests/objectbox-model.json` before opening a fresh store. The `test_store` fixture in `conftest.py` wraps it.
- Tests write DB directories and model JSON files (e.g. `testdata/`, `tests/test-model*.json`) into the working tree; these are artifacts, not fixtures to commit.

## CI

GitHub Actions (`.github/workflows/test.yaml`) runs `make depend && make test` on Linux/Windows/macOS for Python 3.7–3.12, so code must stay compatible with Python 3.7. GitLab CI (`.gitlab-ci.yml`) builds the wheels with `make depend test build` on Linux x64, then tests the built `objectbox` wheel (installed in place of the source packages, which are deleted; the platform's `objectbox-clib` wheel is picked via `--find-links dist`) on Linux x64 (Python 3.7–3.12 Docker images), Linux armv7hf and aarch64, macOS (arm64 runner; the macOS library is universal) and Windows x64.
