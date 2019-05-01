# entity decorator
class _Entity(object):
    def __init__(self, cls, id: int, uid: int):
        self.cls = cls
        self.name: str = cls.__name__
        self.id = id
        self.uid = uid

        # currently, ID and UID are mandatory and are not fetched from the model.json
        if id <= 0:
            raise ValueError("invalid or no 'id; given in the @Entity annotation")

        if uid <= 0:
            raise ValueError("invalid or no 'uid' given in the @Entity annotation")

    def __call__(self):
        return self.cls()


# wrap _Entity to allow @Entity(id=, uid=), i.e. no class argument
def Entity(cls=None, id: int = 0, uid: int = 0):
    if cls:
        return _Entity(cls, id, uid)
    else:
        def wrapper(cls):
            return _Entity(cls, id, uid)

        return wrapper
