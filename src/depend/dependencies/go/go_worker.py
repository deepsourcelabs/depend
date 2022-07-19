"""Functions to handle Go files"""
import json
import logging
import os.path
import platform
import sys
from ctypes import c_char_p, c_void_p, cdll, string_at
from datetime import datetime

from depend.dependencies.dep_types import Result

current_dir = os.path.dirname(__file__)
match platform.system():
    case "Darwin":
        lib_go = cdll.LoadLibrary(os.path.join(current_dir, "darwin/libgomod.dylib"))
    case "Linux":
        lib_go = cdll.LoadLibrary(os.path.join(current_dir, "linux/libgomod.so"))
    case "Windows":
        lib_go = cdll.LoadLibrary(os.path.join(current_dir, "win64/_gomod.dll"))
    case _:
        logging.error("Not supported on current platform")
        sys.exit(-1)

getDepVer = lib_go.getDepVer
getDepVer.argtypes = [c_char_p]
getDepVer.restype = c_void_p
free = lib_go.freeCByte
free.argtypes = [c_void_p]


def handle_go_mod(req_file_data: str) -> Result:
    """
    Parse go.mod file
    :param req_file_data: Content of go.mod
    :return: list of requirement and specs
    """
    res: Result = {
        "import_name": "",
        "lang_ver": [],
        "pkg_name": "",
        "pkg_ver": "",
        "pkg_lic": ["Other"],
        "pkg_err": {},
        "pkg_dep": [],
        "timestamp": datetime.utcnow().isoformat(),
    }
    ptr = getDepVer(req_file_data.encode("utf-8"))
    out = string_at(ptr).decode("utf-8")
    free(ptr)
    d = json.loads(out)
    m = {
        "MinGoVer": "lang_ver",
        "ModPath": "pkg_name",
        "ModVer": "pkg_ver",
        "DepVer": "pkg_dep",
    }
    for k in d:
        if k in m:
            if k == "MinGoVer":
                res[m[k]] = d[k].split(",")  # type: ignore
            elif d[k]:
                res[m[k]] = d[k]  # type: ignore
    res["timestamp"] = datetime.utcnow().isoformat()
    return res
