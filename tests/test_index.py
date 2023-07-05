import objectbox
from objectbox.model import *
from objectbox.model.properties import IndexType
import pytest
from tests.model import TestEntity
from tests.common import (
    autocleanup,
    load_empty_test_objectbox,
)

def test_index_basics():
    ob = load_empty_test_objectbox()
    box = objectbox.Box(ob, TestEntity)

    # create
    object = TestEntity()
    box.put(object)

    # string - default index type is hash
    assert box._entity.properties[1]._index_type == IndexType.hash

    # int64 - default index type is value
    assert box._entity.properties[3]._index_type == IndexType.value

    # int32 - index type overwritten to hash
    assert box._entity.properties[4]._index_type == IndexType.hash

    # int16 - specify index type w/o explicitly enabling index
    assert box._entity.properties[5]._index_type == IndexType.hash

    # bytes - index type overwritten to hash64
    assert box._entity.properties[10]._index_type == IndexType.hash64


def test_index_error():
    @Entity(id=3, uid=3)
    class TestEntityInvalidIndex:
        id = Id(id=1, uid=3001)

        # Cannot set index type when index is False
        try:
            str = Property(str, id=2, uid=3002, index=False, index_type=IndexType.hash)
        except Exception:
            assert pytest.raises(Exception, match='trying to set index type on property of id 2 while index is set to False')