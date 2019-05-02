from objectbox.c import *
import flatbuffers.number_types


# base property
class Property:
    def __init__(self, py_type: type, id: int, uid: int):
        self._is_id = isinstance(self, Id)
        self._id = id
        self._uid = uid
        self._name: str = ""  # set when in Entity.fillProperties()

        self._py_type: type = py_type
        self._ob_type: OBXPropertyType
        self._fb_type: object  # flatbuffers.number_types
        self.__set_basic_type()

        self._flags: OBXPropertyFlags = 0
        self.__set_flags()

    def __set_basic_type(self) -> OBXPropertyType:
        ts = self._py_type
        if ts == str:
            self._ob_type = OBXPropertyType_String
            self._fb_type = flatbuffers.number_types.UOffsetTFlags
        elif ts == int:
            self._ob_type = OBXPropertyType_Long
            self._fb_type = flatbuffers.number_types.Int64Flags
        # TODO support
        # elif ts == bytes or ts == bytearray:
        #     self.__ob_type = OBXPropertyType_ByteVector
        #     self.__fb_type = flatbuffers.number_types.UOffsetTFlags
        elif ts == float:
            self._ob_type = OBXPropertyType_Double
            self._fb_type = flatbuffers.number_types.Float64Flags
        elif ts == bool:
            self._ob_type = OBXPropertyType_Bool
            self._fb_type = flatbuffers.number_types.BoolFlags
        else:
            raise TypeError("unknown property type %s" % ts)

    def __set_flags(self):
        if self._is_id:
            self._flags = OBXPropertyFlags_ID

# ID property (primary key)
class Id(Property):
    def __init__(self, py_type: type = int, id: int = 0, uid: int = 0):
        super(Id, self).__init__(py_type, id, uid)
