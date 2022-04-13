"""Functions to handle Rust dependency files."""
from datetime import datetime

import toml
from pkg_resources import parse_requirements

from dependencies.py.setup_reader import LaxSetupReader, handle_classifiers
import dparse2


def handle_toml(file_data: str) -> dict:
    """
    Parse pyproject or poetry toml files and return required keys
    :param file_data: content of toml
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
    toml_parsed = dict(toml.loads(file_data))
    package_data = toml_parsed.get("package")
    package_dep = toml_parsed.get("dependencies")
    for (ir, spec) in package_dep.items():
        if isinstance(spec, str):
            res["pkg_dep"].append(
                ir + ";" + spec
            )
        else:
            #     TODO handle dict cases
            pass
    res["pkg_name"] = package_data.get("name", "")
    res["pkg_ver"] = package_data.get("version", "")
    res["pkg_lic"] = [package_data.get("license", "Other")]
    classifiers = "\n".join(package_data.get("classifiers", []))
    if classifiers:
        handle_classifiers(classifiers, res)
    return res

def handle_lock(file_data: str, file_name:str)->dict:
    """
    Parses conda.yml tox.ini and Pipfiles
    this function returns only dependencies
    slated for removal once individual cases are handled
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
    df = dparse2.parse(
        file_data,
        file_name=file_name
    )
    for dep in df.dependencies:
        res["pkg_dep"].append(
            dep.name + ";" + str(dep.specs)
        )
    return res

