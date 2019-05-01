from objectbox.c import C
from objectbox.model import Model


class Builder:
    def __init__(self):
        self.__model = Model()

    def model(self, model: Model) -> 'Builder':
        self.__model = model
        pass
