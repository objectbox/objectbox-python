from objectbox.c import *
from objectbox.model import Model
from objectbox.objectbox import ObjectBox


class Builder:
    def __init__(self):
        self._model = Model()
        self._directory = ''

    def directory(self, path: str) -> 'Builder':
        self._directory = path
        return self

    def model(self, model: Model) -> 'Builder':
        self._model = model
        self._model._finish()
        return self

    def build(self) -> 'ObjectBox':
        c_options = OBX_store_options()
        if len(self._directory) > 0:
            c_options.directory = c_str(self._directory)

        c_store = obx_store_open(self._model._c_model, c_options.p())
        return ObjectBox(c_store)
