import objectbox
from tests.model import TestEntity
from tests.common import autocleanup, load_empty_test_objectbox


def test_transactions():
    ob = load_empty_test_objectbox()
    box = objectbox.Box(ob, TestEntity)

    assert box.is_empty()

    with ob.write_tx():
        box.put(TestEntity(str="first"))
        box.put(TestEntity(str="second"))

    assert box.count() == 2

    try:
        with ob.write_tx():
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
        with ob.read_tx():
            box.put(TestEntity(str="third"))

        # exception must be propagated so this line must not execute
        assert 0
    except Exception as err:
        assert "Cannot start a write transaction inside a read only transaction" in str(err)
    finally:
        ob.close()
