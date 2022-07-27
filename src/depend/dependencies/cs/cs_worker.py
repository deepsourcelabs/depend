"""Functions to handle C# dependency files."""
from datetime import datetime

import xmltodict


def findkeys(node, kv):
    """
    Find nested keys by key id
    """
    if isinstance(node, list):
        for i in node:
            for x in findkeys(i, kv):
                yield x
    elif isinstance(node, dict):
        if kv in node:
            yield node[kv]
        for j in node.values():
            for x in findkeys(j, kv):
                yield x


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
    pkg_dep = set()
    for gen_e in findkeys(root.get("dependencies"), "dependency"):
        if isinstance(gen_e, list):
            for dep_e in gen_e:
                dep_entry = dep_e.get("@id") + ";" + dep_e.get("@version")
                pkg_dep.add(dep_entry)
        else:
            dep_entry = gen_e.get("@id") + ";" + gen_e.get("@version")
            pkg_dep.add(dep_entry)
    return pkg_dep, root
