import objectbox
from tests.model import TestEntity
from tests.common import *


def test_transactions(test_store):
    box = test_store.box(TestEntity)

    assert box.is_empty()

    with test_store.write_tx():
        box.put(TestEntity(str="first"))
        box.put(TestEntity(str="second"))

    assert box.count() == 2

    try:
        with test_store.write_tx():
            box.put(TestEntity(str="third"))
            box.put(TestEntity(str="fourth"))
            raise Exception("mission abort!")

        # exception must be propagated so this line must not execute
        assert 0
    except Exception as err:
        assert str(err) == "mission abort!"

    # changes have been rolled back
    assert box.count() == 2

    # can't write in a read TX
    try:
        with test_store.read_tx():
            box.put(TestEntity(str="third"))

        # exception must be propagated so this line must not execute
        assert 0
    except Exception as err:
        assert "Cannot start a write transaction inside a read only transaction" in str(err)
    finally:
        test_store.close()


def test_transactions_closed(test_store):
    box = test_store.box(TestEntity)
    id = box.put(TestEntity(str="first"))

    # Read transactions are closed, also on exceptions: writing works afterwards (same thread)
    with test_store.read_tx():
        assert box.get(id).str == "first"
    try:
        with test_store.read_tx():
            raise KeyError("read abort")
    except KeyError:
        pass
    box.put(TestEntity(str="second"))

    # Also exceptions not derived from Exception roll back a write transaction
    try:
        with test_store.write_tx():
            box.put(TestEntity(str="third"))
            raise KeyboardInterrupt()
    except KeyboardInterrupt:
        pass
    assert box.count() == 2

    # get() in a write transaction sees its changes
    with test_store.write_tx():
        id = box.put(TestEntity(str="fourth"))
        assert box.get(id).str == "fourth"
    assert box.count() == 3
    assert box.get(12345) is None
