# AGENTS.md

This file provides guidance to AI coding agents when working with code in this repository.

## Commands

All `make` targets use (and create if needed) the virtualenv in `.venv` from `requirements.txt`.

- `make depend` — set up venv and download the ObjectBox C shared libraries (`download-c-lib.py`) into `objectbox_clib/lib/<arch>/`. Required once after checkout and whenever the C library version changes.
- `make test` — run all tests (`python -m pytest --capture=no --verbose`)
- `make build` — clean and build the wheels into `dist/`: `objectbox` and `objectbox-clib` (one per platform)
- `make test-fast-flatbuffers-builder` — all tests with the experimental fast FlatBuffers builder in verify mode (`pytest --fast-flatbuffers-builder` or `OBX_TEST_FAST_FLATBUFFERS_BUILDER=1`): every object put by any test is compared byte by byte with the reference
- `make test-flatbuffers-codegen` — the same with the experimental FlatBuffers codegen (`pytest --flatbuffers-codegen` or `OBX_TEST_FLATBUFFERS_CODEGEN=1`)
- `make benchmark` — CRUD benchmark (`benchmark.py`; `BENCHMARK_ARGS=--fast-flatbuffers-builder` or `--flatbuffers-codegen` for the experimental builders)
- Single test: `.venv/bin/python -m pytest tests/test_query.py::test_name -s -v` (the venv gets pytest etc. from `requirements.txt` via any `make` target, e.g. `make depend`)

Run pytest from the repository root: tests import both `common` (via `tests/conftest.py`) and `tests.model`.

There is no linter configured; CONTRIBUTING.md asks for PEP-8 formatting.

## Architecture

Python binding for the ObjectBox C API (objectbox-c) via `ctypes`; objects are serialized with FlatBuffers.

- **`objectbox/c.py`** — all C bindings. Loads the library from the `objectbox_clib` package (`objectbox_clib/lib/<platform.machine()>/`, or `macos-universal`) at import and asserts the core version equals `required_version`. `required_version` is the single source of the C library version (see Packaging). Functions are declared with helpers: `c_fn` (checks result/pointer), `c_fn_rc` (returns `obx_err`, raises via `check_obx_err`), `c_fn_qb_cond`, `c_fn_nocheck`.
- **`objectbox/exceptions.py`** — `DbError` base class plus one subclass per `DbErrorCode`; `create_db_error(code)` maps C error codes to exception classes (message taken from `obx_last_error_message()`).
- **Model definition** (`objectbox/model/`):
  - `@Entity()` (`entity.py`) wraps a user class into an `_Entity` (handles FlatBuffers `_marshal`/`_unmarshal`; `_marshal_builder` is the generic `flatbuffers.Builder` path) and registers it in the global `obx_models_by_name` under a model name (default `"default"`). Property classes used as bare class members (e.g. `name = String`) are instantiated by the decorator.
  - `properties.py` — typed `Property` classes (scalars, vectors/lists, Date, Flex, `HnswIndex` for vector search). Property operators/methods (`==`, `starts_with`, `nearest_neighbor`, …) produce `PropertyQueryCondition`s.
  - `fast_builder.py` — experimental (`objectbox/experimental.py`, off by default): `FastBuilder` produces the same bytes as `_marshal_builder` with the layout precomputed per entity (by alignment residue); it mirrors the Builder's layout rules, so keep it byte-identical (`tests/test_fast_flatbuffers_builder.py`).
  - `codegen.py` — experimental, the alternative to `fast_builder.py` (only one is active: `experimental._flatbuffers_mode`): `CodegenBuilder` generates and `exec`s a marshal function per entity that does what `FastBuilder.marshal` does, unrolled; it uses a `FastBuilder`'s layouts. Changes to `FastBuilder.marshal` must be mirrored in the generated code; the same tests check both. It also generates an unmarshal function, used by `_Entity._unmarshal` in codegen mode, that must return the same values as `_unmarshal_table` (flatbuffers.Table, the reference), so changes to reading go into both.
  - `idsync.py` — assigns IDs/UIDs by syncing the model against an `objectbox-model.json` file (read, matched by UID then name, rewritten from scratch). This is how renames/removals are tracked across schema changes.
- **`Store`** (`store.py`) — opening a store: resolve the model (a `Model` or a model name string → collect registered entities), locate `objectbox-model.json` (explicit `model_json_file`, else the calling module's directory found via the call stack, else `__main__`'s directory, else CWD), run `sync_model` (only once per `Model` and JSON file in a process: `Model._synced_json_file`; models for names are cached in `_models_by_name`), then build `StoreOptions` and call `obx_store_open`. `skip_model_sync=True` opens an existing store without passing the model (schema from the database). Directory prefix `memory:` opens an in-memory DB.
- **`Box`** (`box.py`) — CRUD per entity. `box.query(condition)` returns a `QueryBuilder`; conditions (`condition.py`, combinable with `&`/`|`) are applied onto the C query builder, then `.build()` yields a `Query`.
- **Deprecated API**: `ObjectBox` and `Builder` are thin wrappers around `Store` kept for backward compatibility (`tests/test_deprecated.py`).
- numpy and flatbuffers (which imports numpy) are imported lazily, only where needed (vector/flex properties, the reference FlatBuffers paths); no module-level imports of either (`tests/test_lazy_imports.py`). Use `is_ndarray()` (`c.py`) for type checks and `prop._fb_format` (struct format) instead of `prop._fb_type` outside the reference paths.
- Public API is the flat export list in `objectbox/__init__.py`; the binding version (`version = Version(...)`) is also defined there and used by `setup.py`.

## Packaging

Two pip packages are built from this repository:
- `objectbox` (`setup.py`): the Python binding; depends on the matching `objectbox-clib` version (`==<C version>.*`).
- `objectbox-clib` (`setup-clib.py`, package `objectbox_clib/`): only the C libraries, no Python code. Built as one wheel per platform (wheel platform tags in `PLATFORMS`, so pip picks the platform's library). There is no fallback wheel: other platforms, e.g. Linux armv6l (no manylinux support), are not supported. Versioned like the C library.

`build_info.py` reads the binding version (`objectbox/__init__.py`) and the C library version (`required_version` in `objectbox/c.py`) as text for the build scripts and `download-c-lib.py`. Build scripts must not import `objectbox`: that loads the C library. To bump the C library, only change `required_version`, run `make depend`, and re-check the platform tags in `setup-clib.py` against the new libraries' minimum glibc/macOS versions.

## Tests

- `tests/model.py` defines test entities; `tests/common.py` has `create_test_store()` which deletes the DB dir (`testdata` by default) and `tests/objectbox-model.json` before opening a fresh store. The `test_store` fixture in `conftest.py` wraps it.
- Tests write DB directories and model JSON files (e.g. `testdata/`, `tests/test-model*.json`) into the working tree; these are artifacts, not fixtures to commit.

## CI

GitHub Actions (`.github/workflows/test.yaml`) runs `make depend && make test && make test-fast-flatbuffers-builder && make test-flatbuffers-codegen` on Linux/Windows/macOS for Python 3.7–3.12 (plus Windows ARM64 with Python 3.12), so code must stay compatible with Python 3.7. GitLab CI (`.gitlab-ci.yml`) builds the wheels with `make depend test build` on Linux x64, then tests the built `objectbox` wheel (also with `--fast-flatbuffers-builder` and `--flatbuffers-codegen`; installed in place of the source packages, which are deleted; the platform's `objectbox-clib` wheel is picked via `--find-links dist`) on Linux x64 (Python 3.7–3.12 Docker images), Linux armv7hf and aarch64, macOS (arm64 runner; the macOS library is universal) and Windows x64.
