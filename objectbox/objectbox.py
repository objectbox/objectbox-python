from objectbox.c import *


class ObjectBox:
    def __init__(self, c_store: OBX_store_p):
        self._c_store = c_store

    def __del__(self):
        obx_store_close(self._c_store)
