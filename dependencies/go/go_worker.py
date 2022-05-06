"""Functions to handle Go files"""
import json
import logging
import platform
from ctypes import c_char_p, c_void_p, cdll, string_at

match platform.system():
    case "Darwin":
        lib_go = cdll.LoadLibrary("dependencies/go/darwin/libgomod.dylib")
    case "Linux":
        lib_go = cdll.LoadLibrary("dependencies/go/linux/libgomod.so")
    case "Windows":
        lib_go = cdll.LoadLibrary("dependencies/go/win64/_gomod.dll")
    case _:
        lib_go = None
        logging.error("Not supported on current platform")

getDepVer = lib_go.getDepVer
getDepVer.argtypes = [c_char_p]
getDepVer.restype = c_void_p
free = lib_go.freeCByte
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
