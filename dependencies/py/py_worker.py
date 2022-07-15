"""Functions to handle Python dependency files."""
from datetime import datetime

import dparse2
import packaging.specifiers
import toml
from pkg_resources import parse_requirements

from ..dep_types import Result
from .setup_reader import LaxSetupReader, handle_classifiers


def handle_setup_py(req_file_data: str) -> Result:
    """
    Parse setup.py
    :param req_file_data: Content of setup.py
    :return: dict containing dependency info and specs
    """
    parser = LaxSetupReader()
    return parser.auth_read_setup_py(req_file_data)


def handle_setup_cfg(req_file_data: str) -> Result:
    """
    Parse setup.py
    :param req_file_data: Content of setup.py
    :return: dict containing dependency info and specs
    """
    parser = LaxSetupReader()
    return parser.read_setup_cfg(req_file_data)


def handle_toml(file_data: str) -> Result:
    """
    Parse pyproject or poetry toml files and return required keys
    :param file_data: content of toml
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
    toml_parsed = dict(toml.loads(file_data))
    package_data = toml_parsed.get("package")
    if not package_data:
        package_data = toml_parsed.get("tool", {}).get("poetry", {})
        # 'es-core-news-sm', {'url': ''} ignored
        package_dep = [
            ";".join(dep)
            for dep in package_data.get("dependencies", {}).items()
            if isinstance(dep[-1], str)
        ]
        res["pkg_dep"] = package_dep
    else:
        package_dep = package_data.get("dependencies")
        if isinstance(package_dep, dict):
            res["pkg_dep"] = []
        elif package_dep:
            install_reqs = parse_requirements("\n".join(package_dep))
            ir: packaging.specifiers.SpecifierSet
            for ir in install_reqs:
                res["pkg_dep"].append(str(ir.key) + ";" + str(ir.specifier))
    res["pkg_name"] = package_data.get("name", "")
    res["pkg_ver"] = package_data.get("version", "")
    res["pkg_lic"] = [package_data.get("license", "Other")]
    classifiers = "\n".join(package_data.get("classifiers", []))
    if classifiers:
        handle_classifiers(classifiers, res)
    return res


def handle_otherpy(file_data: str, file_name: str) -> Result:
    """
    Parses conda.yml tox.ini and Pipfiles
    this function returns only dependencies
    slated for removal once individual cases are handled
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
    df = dparse2.parse(file_data, file_name=file_name)
    for dep in df.dependencies:
        res["pkg_dep"].append(dep.name + ";" + str(dep.specs))
    return res
