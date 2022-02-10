"""Interface with compiled code"""
from ctypes import cdll, c_char_p, c_void_p

libgo = cdll.LoadLibrary("lib/_gomod.so")
getDepVer = libgo.getDepVer
getDepVer.argtypes = [c_char_p]
getDepVer.restype = c_void_p
free = libgo.freeCByte
free.argtypes = [c_void_p]
