import objectbox
from tests.common import autocleanup, load_empty_test_objectbox, assert_equal


def test_version():
    info = objectbox.version_info()
    assert len(info) > 10


def test_open():
    load_empty_test_objectbox()
