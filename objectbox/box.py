from objectbox.model.entity import _Entity
from objectbox.objectbox import ObjectBox
from objectbox.c import *


class Box:
    def __init__(self, ob: ObjectBox, entity: _Entity):
        if not isinstance(entity, _Entity):
            raise Exception("Given type is not an Entity")

        self._ob = ob
        self._entity = entity
        self._c_box = obx_box(ob._c_store, entity.id)

    def is_empty(self) -> bool:
        is_empty = ctypes.c_bool()
        obx_box_is_empty(self._c_box, ctypes.byref(is_empty))
        return bool(is_empty.value)

    def count(self, limit: int = 0) -> int:
        count = ctypes.c_uint64()
        obx_box_count(self._c_box, limit, ctypes.byref(count))
        return int(count.value)

    def put(self, object) -> int:
        id = object_id = self._entity.get_object_id(object)

        if not id:
            id = obx_box_id_for_put(self._c_box, 0)

        data = self._entity.marshal(object, id)
        obx_box_put(self._c_box, id, bytes(data), len(data), OBXPutMode_PUT)

        if id != object_id:
            self._entity.set_object_id(object, id)
        return id

    def get(self, id: int):
        c_data = ctypes.c_void_p()
        c_size = ctypes.c_size_t()
        obx_box_get(self._c_box, id, ctypes.byref(c_data), ctypes.byref(c_size))

        # TODO verify which of the following two approaches is better.

        # slice the data from the pointer
        # data = ctypes.cast(c_data, ctypes.POINTER(ctypes.c_char))[:c_size.value]

        # create a memory view
        data = memoryview(ctypes.cast(c_data, ctypes.POINTER(ctypes.c_ubyte * c_size.value))[0]).tobytes()

        return self._entity.unmarshal(data)

    def remove(self, id: int):
        obx_box_remove(self._c_box, id)