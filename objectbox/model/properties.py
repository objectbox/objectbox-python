class Property:
    __is_id: bool
    __py_type: type

    def __init__(self, py_type: type):
        self.__is_id = isinstance(self, Id)
        self.__py_type = py_type


class Id(Property):
    def __init__(self, py_type: type = int):
        super(Id, self).__init__(py_type)
