#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import gc
import weakref

import pytest

import objectbox
from objectbox.exceptions import DbError, FeatureNotAvailable, IllegalArgumentError, IllegalStateError, NotFoundError
from tests.common import create_test_store
from tests.model import TestEntity


def test_version():
    assert objectbox.version.major == 5  # update for major version changes
    assert objectbox.version.minor >= 0

    assert objectbox.version_core.major == 5  # update for major version changes
    assert objectbox.version_core.minor >= 0

    info = objectbox.version_info()
    print("\nVersion found:", info)
    assert len(info) > 10
    assert str(objectbox.version) in info
    assert str(objectbox.version_core) in info


def test_open():
    store = create_test_store()
    store.close()


def test_store_used_after_close(capfd):
    """ Using a closed store, or a box or query of it, raises IllegalStateError("Store is closed"); this used to fail
    with misleading errors (e.g. "Argument "store" must not be null") or used the freed C store. """
    store = create_test_store()
    box = store.box(TestEntity)
    id = box.put(TestEntity(str="foo"))
    query = box.query(TestEntity.str.equals("foo")).build()
    store.close()
    store.close()  # Closing again does nothing

    uses = [
        lambda: store.box(TestEntity),
        lambda: store.read_tx(),
        lambda: store.write_tx(),
        lambda: box.get(id),
        lambda: box.get_many([id]),
        lambda: box.get_all(),
        lambda: box.put(TestEntity(str="bar")),
        lambda: box.put([TestEntity(str="bar"), TestEntity(str="baz")]),
        lambda: box.update(TestEntity(id=id, str="bar")),
        lambda: box.contains(id),
        lambda: box.count(),
        lambda: box.is_empty(),
        lambda: box.remove(id),
        lambda: box.remove_all(),
        lambda: box.query(),
    ]
    for use in uses:
        with pytest.raises(IllegalStateError, match="Store is closed$"):
            use()
    for use in (query.find, query.count):
        with pytest.raises(IllegalStateError, match="Store is closed$"):
            use()
    assert "Irrecoverable" not in capfd.readouterr().err  # The C library detected no use of a dead store


def test_store_with_and_is_closed():
    with create_test_store() as store:
        assert not store.is_closed()
        store.box(TestEntity).put(TestEntity(str="foo"))
    assert store.is_closed()

    with pytest.raises(KeyError):
        with create_test_store(clear_db=False) as store:  # Reopens: the store was closed
            assert store.box(TestEntity).count() == 1
            raise KeyError()
    assert store.is_closed()  # Also closed on exceptions

    store = create_test_store(clear_db=False)
    store.close()
    assert store.is_closed()


def test_store_closed_when_dropped():
    """A store that is no longer referenced must be closed right away, without relying on the cyclic GC."""
    gc_was_enabled = gc.isenabled()
    gc.disable()
    try:
        store = create_test_store()
        store_ref = weakref.ref(store)
        del store
        assert store_ref() is None
        # Reopen without deleting the DB files first; that would hide a still open store on Linux (not on Windows)
        store = create_test_store(clear_db=False)  # Raises if the previous store at the same path is still open
        store.close()
    finally:
        if gc_was_enabled:
            gc.enable()


def test_not_found_exception():
    try:
        raise NotFoundError()
    except DbError as e:
        assert e.code == 404


def test_exception_message_and_builtin_bases():
    e = IllegalStateError("Store is closed")
    assert e.message == "Store is closed"
    assert str(e) == "10001 (OBX_ERROR_ILLEGAL_STATE) - Store is closed"
    assert isinstance(e, RuntimeError)
    assert isinstance(IllegalArgumentError("x"), ValueError)
    assert isinstance(FeatureNotAvailable("x"), RuntimeError)
    assert issubclass(IllegalArgumentError, DbError) and issubclass(FeatureNotAvailable, DbError)


def test_c_error_is_builtin_exception(test_store):
    # Errors raised by the C library can also be caught as the matching built-in exception
    with pytest.raises(ValueError, match="OBX_ERROR_ILLEGAL_ARGUMENT") as exc_info:
        test_store.box(TestEntity).get(0)
    assert type(exc_info.value) is IllegalArgumentError


def test_error_types(test_store):
    """ Wrong arguments raise TypeError or IllegalArgumentError (a ValueError), not a plain Exception, an
    AttributeError or a ctypes.ArgumentError. """
    from tests.model import TestEntityDatetime, VectorEntity
    from objectbox.exceptions import create_db_error
    box = test_store.box(TestEntity)
    id = box.put(TestEntity(str="foo"))
    other = TestEntityDatetime()

    with pytest.raises(TypeError, match="Expected an entity"):
        objectbox.Box(test_store, object())
    with pytest.raises(TypeError, match="Expected an object of entity TestEntity"):
        box.put(other)  # AttributeError before
    with pytest.raises(TypeError, match="Expected an object of entity TestEntity"):
        box.put([TestEntity(str="bar"), other])
    assert box.count() == 1
    with pytest.raises(TypeError, match="Expected an object of entity TestEntity"):
        box.update(other)
    with pytest.raises(IllegalArgumentError, match="Cannot update an object without an ID"):
        box.update(TestEntity(str="new"))
    for invalid in ("1", other, 1.0):
        with pytest.raises(TypeError, match=r"Expected an ID \(int\) or an object of entity TestEntity"):
            box.remove(invalid)  # ctypes.ArgumentError before
    assert box.count() == 1

    with pytest.raises(TypeError, match="Property int64 takes int values in conditions, got '1'"):
        TestEntity.int64.equals("1")  # KeyError before
    with pytest.raises(TypeError, match="Unsupported type for 'EQ'"):
        box.query(TestEntity.str.equals(1.5))
    with pytest.raises(IllegalArgumentError, match="query_vector can't be empty"):
        test_store.box(VectorEntity).query(VectorEntity.vector_euclidean.nearest_neighbors([], 1))
    with pytest.raises(TypeError, match="has no property \"nope\""):
        TestEntity(nope=1)
    with pytest.raises(TypeError, match="The given type is not an Entity"):
        objectbox.Model().entity(object())
    query = box.query(TestEntity.str.equals("foo")).build()
    with pytest.raises(IllegalArgumentError, match="Property \"nope\" not found"):
        query.set_parameter("nope", "x")

    # A C error code unknown to Python is a DbError with that code
    error = create_db_error(12345)
    assert type(error) is DbError and error.code == 12345 and str(error).startswith("12345 - ")
    assert type(create_db_error(10002)) is IllegalArgumentError


def test_error_hierarchy():
    """ Like Java and Dart: unique violations are constraint violations, corrupt pages a corrupt file. """
    import builtins
    from objectbox.c import DbErrorCode
    from objectbox.exceptions import (create_db_error, ConstraintViolatedError, UniqueViolatedError, FileCorruptError,
                                      FilePagesCorruptError, FeatureNotAvailableError, TimeoutError)
    assert issubclass(UniqueViolatedError, ConstraintViolatedError)
    assert issubclass(FilePagesCorruptError, FileCorruptError)
    assert FeatureNotAvailable is FeatureNotAvailableError  # The old name still works
    assert issubclass(FeatureNotAvailableError, RuntimeError)
    assert issubclass(TimeoutError, builtins.TimeoutError) and issubclass(TimeoutError, DbError)

    # Every error code is created as its most specific class (also subclasses of subclasses)
    assert type(create_db_error(DbErrorCode.OBX_ERROR_UNIQUE_VIOLATED)) is UniqueViolatedError
    assert type(create_db_error(DbErrorCode.OBX_ERROR_CONSTRAINT_VIOLATED)) is ConstraintViolatedError
    assert type(create_db_error(DbErrorCode.OBX_ERROR_FILE_PAGES_CORRUPT)) is FilePagesCorruptError
    for code in DbErrorCode:
        if code != DbErrorCode.OBX_SUCCESS:
            error = create_db_error(code)
            assert type(error) is not DbError and error.code == code


def test_store_box_cached(test_store):
    """ store.box() returns the same Box per entity (like Java and Dart): no Box creation per call. """
    from tests.model import TestEntityDatetime
    box = test_store.box(TestEntity)
    assert test_store.box(TestEntity) is box
    assert test_store.box(TestEntityDatetime) is not box
    assert test_store.box(TestEntityDatetime) is test_store.box(TestEntityDatetime)
    id = box.put(TestEntity(str="foo"))
    assert test_store.box(TestEntity).get(id).str == "foo"
    with pytest.raises(TypeError, match="Expected an entity"):
        test_store.box(object())

    test_store.close()
    with pytest.raises(IllegalStateError, match="Store is closed$"):
        test_store.box(TestEntity)  # Not the cached box
    with pytest.raises(IllegalStateError, match="Store is closed$"):
        box.count()
    assert test_store._boxes == {}  # Released on close

