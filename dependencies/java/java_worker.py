"""Functions to handle Java dependency files."""
import xmltodict
from datetime import datetime


def handle_pom_xml(req_file_data: str) -> dict:
    """
    Parse required info from pom.xml
    :param req_file_data: Content of pom.xml
    """
    res = {
        "lang_ver": [],
        "pkg_name": "",
        "pkg_ver": "",
        "pkg_lic": ["Other"],
        "pkg_err": {},
        "pkg_dep": [],
        'timestamp': datetime.utcnow().isoformat()
    }
    root = xmltodict.parse(req_file_data).get("project")
    res["pkg_name"] = root.get("groupId") +":"+ root.get("artifactId")
    res["pkg_ver"] = root.get("version")
    pkg_dep = []
    for dep in root.get("dependencies").get("dependency"):
        pkg_dep.append(
            dep.get("groupId") +":"+ dep.get("artifactId")
            +";"+ dep.get("version")
        )
    res["pkg_dep"] = pkg_dep
    return res
