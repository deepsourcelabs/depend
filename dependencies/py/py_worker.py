"""Functions to handle Python files"""
import toml
from pkg_resources import parse_requirements

from dependencies.py.setup_reader import LaxSetupReader
from dependencies.py.setup_reader import handle_classifiers


def handle_requirements_txt(req_file_data: str) -> dict:
    """
    Parse requirements file
    :param req_file_data: Content of requirements.txt
    :return: list of requirement and specs
    """
    res = {
        "lang_ver": "",
        "pkg_name": "",
        "pkg_ver": "",
        "pkg_lic": "",
        "pkg_err": "",
        "pkg_dep": [],
    }
    install_reqs = parse_requirements(req_file_data)
    for ir in install_reqs:
        for spec in ir.specs:
            res["pkg_dep"].append(
                str(ir.key) + ";" +
                str(spec[1]) + ";" + str(spec[0])
            )
    return res


def handle_setup_py(req_file_data: str) -> dict:
    """
    Parse setup.py
    :param req_file_data: Content of setup.py
    :return: dict containing dependency info and specs
    """
    parser = LaxSetupReader()
    return parser.read_setup_py(req_file_data)


def handle_setup_cfg(req_file_data: str) -> dict:
    """
    Parse setup.py
    :param req_file_data: Content of setup.py
    :return: dict containing dependency info and specs
    """
    parser = LaxSetupReader()
    return parser.read_setup_cfg(req_file_data)


def handle_toml(file_data: str) -> dict:
    """
    Parse pyproject or poetry toml files and return required keys
    :param file_data: content of toml
    """
    res = {
        "lang_ver": "",
        "pkg_name": "",
        "pkg_ver": "",
        "pkg_lic": "",
        "pkg_err": "",
        "pkg_dep": [],
    }
    toml_parsed = dict(toml.loads(file_data))
    package_data = toml_parsed.get("package")
    if not package_data:
        package_data = toml_parsed.get("tool", {}).get("poetry", {})
        # 'es-core-news-sm', {'url': ''} ignored
        package_dep = [
            ";".join(dep) for dep
            in package_data.get("dependencies", {}).items()
            if isinstance(dep[-1], str)
        ]
        res["pkg_dep"] = package_dep
    else:
        package_dep = package_data.get("dependencies")
        if isinstance(package_dep, dict):
            res["pkg_dep"] = []
        else:
            install_reqs = parse_requirements("\n".join(package_dep))
            for ir in install_reqs:
                for spec in ir.specs:
                    res["pkg_dep"].append(
                        str(ir.key) + ";" +
                        str(spec[1]) + ";" + str(spec[0])
                    )
    res["pkg_name"] = package_data.get("name", "")
    res["pkg_ver"] = package_data.get("version", "")
    res["pkg_lic"] = package_data.get("license", "")
    classifiers = "\n".join(package_data.get("classifiers", []))
    if classifiers:
        handle_classifiers(classifiers, res)
    return res
