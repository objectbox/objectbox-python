import ctypes.util

# initialize the C library
C = ctypes.CDLL(ctypes.util.find_library("objectbox"))
