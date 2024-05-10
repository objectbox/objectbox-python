import objectbox
from tests.model import TestEntity
from tests.common import *


def test_transactions():
    store = load_empty_test_default_store()
    box = store.box(TestEntity)

    assert box.is_empty()

    with store.write_tx():
        box.put(TestEntity(str="first"))
        box.put(TestEntity(str="second"))

    assert box.count() == 2

    try:
        with store.write_tx():
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
        with store.read_tx():
            box.put(TestEntity(str="third"))

        # exception must be propagated so this line must not execute
        assert 0
    except Exception as err:
        assert "Cannot start a write transaction inside a read only transaction" in str(err)
    finally:
        store.close()
