import pytest
import tests.common
import objectbox
import objectbox.store_options 

def test_deprecated_ObjectBox():
    model = tests.common.create_default_model()
    model._finish()
    options = objectbox.store_options.StoreOptions()
    options.model(model)
    c_store = objectbox.c.obx_store_open(options._c_handle)
    with pytest.deprecated_call():
        ob = objectbox.objectbox.ObjectBox(c_store) 
    
