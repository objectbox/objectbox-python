import tests.common
from objectbox import ObjectBox
from objectbox.c import *
from objectbox.model.idsync import sync_model
from objectbox.store_options import StoreOptions
from tests.common import *

def test_deprecated_ObjectBox():
    Store.remove_db_files("testdata")
    remove_json_model_file()

    model = tests.common.create_default_model()
    sync_model(model)  # It expects IDs to be already assigned

    options = StoreOptions()
    options.model(model)
    options.directory("testdata")
    c_store = obx_store_open(options._c_handle)
    with pytest.deprecated_call():
        ob = ObjectBox(c_store)
    box = objectbox.Box(ob, TestEntity)
    assert box.count() == 0


def test_deprecated_Builder():
    Store.remove_db_files("testdata")
    remove_json_model_file()

    model = tests.common.create_default_model()
    with pytest.deprecated_call():
        ob = objectbox.Builder().model(model).directory("testdata").build()
