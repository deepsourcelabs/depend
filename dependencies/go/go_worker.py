"""Functions to handle Go files"""
import json
from ctypes import cdll, c_char_p, c_void_p, string_at

libgo = cdll.LoadLibrary("dependencies/go/_gomod.so")
getDepVer = libgo.getDepVer
getDepVer.argtypes = [c_char_p]
getDepVer.restype = c_void_p
free = libgo.freeCByte
free.argtypes = [c_void_p]


def handle_go_mod(req_file_data: str) -> dict:
    """
    Parse go.mod file
    :param req_file_data: Content of go.mod
    :return: list of requirement and specs
    """
    ptr = getDepVer(
        req_file_data.encode('utf-8')
    )
    out = string_at(ptr).decode('utf-8')
    free(ptr)
    return json.loads(out)
