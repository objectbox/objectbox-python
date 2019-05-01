class Property:
    __slots__ = ['is_id', 'py_type']

    def __init__(self, py_type: type):
        self.is_id = isinstance(self, Id)
        self.py_type = py_type


class Id(Property):
    def __init__(self, py_type: type = int):
        super(Id, self).__init__(py_type)
