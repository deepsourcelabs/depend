"""Functions to handle C# dependency files."""
from datetime import datetime
from typing import OrderedDict

import xmltodict


def handle_nuspec(req_file_data: str) -> dict:
    """
    Parse required info from .nuspec
    :param req_file_data: Content of pom.xml
    """
    res = {
        "lang_ver": [],
        "pkg_name": "",
        "pkg_ver": "",
        "pkg_lic": ["Other"],
        "pkg_err": {},
        "pkg_dep": [],
        "timestamp": datetime.utcnow().isoformat(),
    }
    parse_nuspec(req_file_data, res)
    return res


def parse_nuspec(req_file_data, result):
    """Get data frim .nuspec files"""
    root = xmltodict.parse(req_file_data).get("package", {}).get("metadata")
    result["pkg_name"] = root.get("id")
    result["pkg_ver"] = root.get("version")
    # ignores "file" type
    if root.get("license", {}).get("@type") == "expression":
        result["pkg_lic"] = [root.get("license", {}).get("#text")]
    dep_info = root.get("dependencies")
    dep_set = set()

    if dep_info and "group" in dep_info:
        # Dependencies Group
        for group in dep_info["group"]:
            if group and "dependency" in group:
                dep_set = dep_set.union(handle_nuspec_dep(group["dependency"]))
    elif dep_info and "dependency" in dep_info:
        # Dependencies element
        dep_set = handle_nuspec_dep(dep_info["dependency"])
    result["pkg_dep"] = list(dep_set)
    return root


def handle_nuspec_dep(dep_list_obj: OrderedDict):
    """Convert dependency specification in nuspec to parsable string"""
    pkg_dep = set()
    if isinstance(dep_list_obj, list):
        for dep in dep_list_obj:
            dep_entry = dep.get("@id") + ";" + dep.get("@version")
            pkg_dep.add(dep_entry)
    else:
        dep_entry = dep_list_obj.get("@id") + ";" + dep_list_obj.get("@version")
        pkg_dep.add(dep_entry)
    return pkg_dep
