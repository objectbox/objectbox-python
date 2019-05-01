from typing import List, Dict

from objectbox.model.properties import Property


# entity decorator
class _Entity(object):
    def __init__(self, cls, id: int, uid: int):
        # currently, ID and UID are mandatory and are not fetched from the model.json
        if id <= 0:
            raise ValueError("invalid or no 'id; given in the @Entity annotation")

        if uid <= 0:
            raise ValueError("invalid or no 'uid' given in the @Entity annotation")

        self.cls = cls
        self.name: str = cls.__name__
        self.id = id
        self.uid = uid

        self.properties: List[Property] = list()
        self.fillProperties()

    def __call__(self):
        return self.cls()

    def fillProperties(self):
        # TODO allow subclassing and support entities with __slots__ defined
        variables = dict(vars(self.cls))

        # filter only subclasses of Property
        variables = {k: v for k, v in variables.items() if issubclass(type(v), Property)}

        for k, v in variables.items():
            v.__name = k
            self.properties.append(v)


# wrap _Entity to allow @Entity(id=, uid=), i.e. no class argument
def Entity(cls=None, id: int = 0, uid: int = 0):
    if cls:
        return _Entity(cls, id, uid)
    else:
        def wrapper(cls):
            return _Entity(cls, id, uid)

        return wrapper
