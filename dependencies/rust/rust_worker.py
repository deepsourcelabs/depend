"""Functions to handle Rust dependency files."""
import re
from datetime import datetime

import toml


def handle_cargo_toml(file_data: str) -> dict:
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
        "timestamp": datetime.utcnow().isoformat(),
    }
    toml_parsed = dict(toml.loads(file_data))
    package_data = toml_parsed.get("package")
    package_dep = toml_parsed.get("dependencies")
    for (ir, spec) in package_dep.items():
        if isinstance(spec, str):
            res["pkg_dep"].append(ir + ";" + spec.split(",")[0])
        elif isinstance(spec, dict):
            if git_url := spec.get("git", None):
                git_branch = git_url + "||" + spec.get("branch", "")
                res["pkg_dep"].append(ir + ";" + git_branch)
    res["pkg_name"] = package_data.get("name", "")
    res["pkg_ver"] = package_data.get("version", "")
    res["pkg_lic"] = [package_data.get("license", "Other")]
    return res


def handle_lock(file_data: str) -> dict:
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
        "timestamp": datetime.utcnow().isoformat(),
    }
    dependencies_regex = re.compile(
        r'name = \"([^"]+)\"[\n\r]version = \"([^"]+)\"', re.MULTILINE
    )
    matches = [m.groups() for m in dependencies_regex.finditer(file_data)]
    for name, specs in matches:
        res["pkg_dep"].append(name + ";" + str(specs))
    return res
