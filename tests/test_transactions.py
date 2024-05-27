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
