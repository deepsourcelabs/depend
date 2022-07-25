"""Helper functions for Python Dependencies"""
from datetime import datetime

import packaging.specifiers
from pkg_resources import parse_requirements

from depend.dependencies.dep_types import Result


def handle_requirements_txt(req_file_data: str) -> Result:
    """
    Parse requirements file
    :param req_file_data: Content of requirements.txt
    :return: list of requirement and specs
    """
    res: Result = {
        "import_name": "",
        "lang_ver": [],
        "pkg_name": "",
        "pkg_ver": "",
        "pkg_lic": ["Other"],
        "pkg_err": {},
        "pkg_dep": None,
        "timestamp": datetime.utcnow().isoformat(),
    }
    install_reqs = parse_requirements(req_file_data)
    ir: packaging.specifiers.SpecifierSet
    pkg_dep = []
    for ir in install_reqs:
        if not ir.specs:
            pkg_dep.append(str(ir.key) + ";" + "latest")
        else:
            pkg_dep.append(str(ir.key) + ";" + str(ir.specifier))
    if len(pkg_dep) > 0:
        res["pkg_dep"] = pkg_dep
    return res
