"""Functions to handle Go files"""
import json
import logging
import platform
from ctypes import c_char_p, c_void_p, cdll, string_at
from datetime import datetime


match platform.system():
    case "Linux":
        lib_go = cdll.LoadLibrary("dependencies/go/linux/_gomod.so")
    case "Windows":
        lib_go = cdll.LoadLibrary("dependencies/go/win32/_gomod.so")
    case _:
        lib_go = None
        logging.error("Not compiled for Darwin")

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
    ptr = getDepVer(req_file_data.encode("utf-8"))
    out = string_at(ptr).decode("utf-8")
    free(ptr)
    d = json.loads(out)
    m = {
        "Min_go_ver": "lang_ver",
        "ModPath": "pkg_name",
        "ModVer": "pkg_ver",
        "Dep_ver": "pkg_dep",
    }
    data_available = {m[k]: d[k] for k in d if k in m}
    data_available["pkg_err"] = {"pkg_dep": d.get("ModDeprecated", "")}
    data_available["lang_ver"] = data_available.get("lang_ver", "").split(",")
    data_available["pkg_lic"] = ["Other"]
    data_available["timestamp"] = datetime.utcnow().isoformat()
    return data_available
