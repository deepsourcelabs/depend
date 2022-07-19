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
    root = xmltodict.parse(req_file_data).get("package", {}).get("metadata")
    res["pkg_name"] = root.get("id")
    res["pkg_ver"] = root.get("version")
    # ignores "file" type
    if root.get("license", {}).get("@type") == "expression":
        res["pkg_lic"] = [root.get("license", {}).get("#text")]
    pkg_dep = []
    for dep in sum(list(findkeys(root.get("dependencies"), "dependency")), []):
        pkg_dep.append(dep.get("@id") + ";" + dep.get("@version"))
    res["pkg_dep"] = pkg_dep
    return res
