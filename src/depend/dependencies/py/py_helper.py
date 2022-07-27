"""Helper functions for Python Dependencies"""
from datetime import datetime

import packaging
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
        "pkg_dep": get_py_dep_from_iterable(req_file_data),
        "timestamp": datetime.utcnow().isoformat(),
    }
    return res


def get_py_dep_from_iterable(api_depend):
    install_reqs = parse_requirements(api_depend)
    ir: packaging.specifiers.SpecifierSet
    pkg_dep = []
    for ir in install_reqs:
        if not ir.specs:
            pkg_dep.append(str(ir.key) + ";" + "latest")
        else:
            pkg_dep.append(str(ir.key) + ";" + str(ir.specifier))
    return pkg_dep
