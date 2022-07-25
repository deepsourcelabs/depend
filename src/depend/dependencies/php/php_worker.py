"""Functions to handle PHP files"""
import json
from datetime import datetime

from depend.dependencies.dep_types import Result


def handle_composer_json(req_file_data: str) -> Result:
    """
    Parse composer json files required by php
    :param req_file_data: Content of package.json
    :return: list of requirement and specs
    """
    package_data = json.loads(req_file_data)
    dep_data = package_data.get("require", {})
    lang_ver = dep_data.pop("php", "")
    filter_dict: Result = {
        "import_name": "",
        "lang_ver": [lang_ver],
        "pkg_name": package_data.get("name", ""),
        "pkg_ver": package_data.get("version", ""),
        "pkg_lic": package_data.get("license", "Other").split(","),
        "pkg_dep": [key + ";" + value for (key, value) in dep_data.items()],
        "pkg_err": {},
        "timestamp": datetime.utcnow().isoformat(),
    }
    return filter_dict
