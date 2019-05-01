from objectbox.c import *
import flatbuffers.number_types


# base property
class Property:
    def __init__(self, py_type: type, id: int, uid: int):
        self.__is_id = isinstance(self, Id)
        self.__py_type = py_type
        self.__id = id
        self.__uid = uid
        self.__name: str = ""  # set when in Entity.fillProperties()

        self.__ob_type: OBXPropertyType
        self.__fb_type: object  # flatbuffers.number_types
        self._set_basic_type()

    def _set_basic_type(self) -> OBXPropertyType:
        ts = self.__py_type
        if ts == str:
            self.__ob_type = OBXPropertyType_String
            self.__fb_type = flatbuffers.number_types.UOffsetTFlags
        elif ts == int:
            self.__ob_type = OBXPropertyType_Long
            self.__fb_type = flatbuffers.number_types.Int64Flags
        # TODO support
        # elif ts == bytes or ts == bytearray:
        #     self.__ob_type = OBXPropertyType_ByteVector
        #     self.__fb_type = flatbuffers.number_types.UOffsetTFlags
        elif ts == float:
            self.__ob_type = OBXPropertyType_Double
            self.__fb_type = flatbuffers.number_types.Float64Flags
        elif ts == bool:
            self.__ob_type = OBXPropertyType_Bool
            self.__fb_type = flatbuffers.number_types.BoolFlags
        else:
            raise TypeError("unknown property type %s" % ts)


# ID property (primary key)
class Id(Property):
    def __init__(self, py_type: type = int, id: int = 0, uid: int = 0):
        super(Id, self).__init__(py_type, id, uid)
