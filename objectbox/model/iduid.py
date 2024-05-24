class IdUid:
    __slots__ = 'id', 'uid'

    def __init__(self, id_: int, uid: int):
        self.id = id_
        self.uid = uid

    def is_assigned(self):
        """ Checks that both ID and UID are assigned. Shall be true after the model is synced. """
        return self.id != 0 and self.uid != 0

    def __bool__(self):
        return self.is_assigned()

    def __eq__(self, rhs: 'IdUid'):
        return self.id == rhs.id and self.uid == rhs.uid

    def __str__(self):
        return f"{self.id}:{self.uid}"

    @staticmethod
    def from_str(str_: str):
        """ Parses IdUid from a string formatted like: "id:uid" """
        tmp = str_.split(":")
        return IdUid(int(tmp[0]), int(tmp[1]))

    @staticmethod
    def unassigned():
        return IdUid(0, 0)
