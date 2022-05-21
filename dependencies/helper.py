"""Helper Functions for Inspector."""
import re
from typing import List

import jmespath
import requests
from bs4 import BeautifulSoup

from dep_types import Result
from error import FileNotSupportedError

from .go.go_worker import handle_go_mod
from .js.js_worker import handle_json, handle_yarn_lock
from .py.py_helper import handle_requirements_txt
from .py.py_worker import handle_otherpy, handle_setup_cfg, handle_setup_py, handle_toml
from .rust.rust_worker import handle_c_toml, handle_lock


def parse_license(license_file: str, license_dict: dict) -> List[str]:
    """
    Check license file content and return the possible license type.
    :param license_file: String containing license file content
    :param license_dict: Dictionary mapping license files and unique substring
    :return: Detected license type as a String, `Other` if failed to detect
    """
    licenses = [
        license_str for lic, license_str in license_dict.items() if lic in license_file
    ]
    return licenses or ["Other"]


def handle_dep_file(
    file_name: str,
    file_content: str,
) -> Result:
    """
    Parses contents of requirement file and returns useful insights
    :param file_name: name of requirement file
    :param file_content: content of the file
    :return: key features for murdock
    """
    file_extension = file_name.split(".")[-1]
    if file_name in ["conda.yml", "tox.ini", "Pipfile", "Pipfile.lock"]:
        return handle_otherpy(file_content, file_name)
    match file_extension:
        case "mod":
            return handle_go_mod(file_content)
        case "json":
            return handle_json(file_content)
        case ["conda.yml", "tox.ini", "Pipfile", "Pipfile.lock"]:
            return handle_otherpy(file_content, file_name)
        case "lock":
            if file_name == "Cargo.lock":
                return handle_lock(file_content)
            return handle_yarn_lock(file_content)
        case "txt":
            return handle_requirements_txt(file_content)
        case "toml":
            if file_name == "Cargo.toml":
                return handle_c_toml(file_content)
            return handle_toml(file_content)
        case "py":
            return handle_setup_py(file_content)
        case "cfg":
            return handle_setup_cfg(file_content)
        case _:
            raise FileNotSupportedError(file_name)


def parse_dep_response(
    ecs: list[Result],
) -> dict:
    """
    Constructs required schema from extracted fields
    :param ecs: list of extracted content to fix
    :return: final result for a package as per schema
    """
    main_key = ecs[0].get("pkg_name")
    final_response = {
        main_key: {
            "versions": {
                ec.get("pkg_ver"): {
                    "import_name": ec.get("import_name") or main_key,
                    "lang_ver": ec.get("lang_ver") or [],
                    "pkg_lic": [ec.get("pkg_lic")]
                    if isinstance(ec.get("pkg_lic"), str)
                    else ec.get("pkg_lic"),
                    "pkg_err": ec.get("pkg_err") or {},
                    "pkg_dep": ec.get("pkg_dep") or [],
                    "timestamp": ec.get("timestamp"),
                }
                for ec in ecs
            }
        }
    }
    return final_response


def handle_pypi(api_response: requests.Response, queries: dict, result: Result):
    """
    Take api response and return required results object
    :param api_response: response from requests get
    :param queries: compiled jmespath queries
    :param result: object to mutate
    """
    version_q: jmespath.parser.ParsedResult = queries["version"]
    license_q: jmespath.parser.ParsedResult = queries["license"]
    dependencies_q: jmespath.parser.ParsedResult = queries["dependency"]
    repo_q: jmespath.parser.ParsedResult = queries["repo"]
    if api_response.status_code == 404:
        return ""
    data = api_response.json()
    result["pkg_ver"] = version_q.search(data) or ""
    result["pkg_lic"] = [license_q.search(data) or "Other"]
    req_file_data = "\n".join(dependencies_q.search(data) or "")
    result["pkg_dep"] = handle_requirements_txt(req_file_data).get("pkg_dep", [])
    repo = repo_q.search(data) or ""
    return repo


def handle_npmjs(api_response: requests.Response, queries: dict, result: Result):
    """
    Take api response and return required results object
    :param api_response: response from requests get
    :param queries: compiled jmespath queries
    :param result: object to mutate
    """
    if api_response.status_code == 404:
        return ""
    data = api_response.json()
    version_q: jmespath.parser.ParsedResult = queries["version"]
    license_q: jmespath.parser.ParsedResult = queries["license"]
    dependencies_q: jmespath.parser.ParsedResult = queries["dependency"]
    repo_q: jmespath.parser.ParsedResult = queries["repo"]
    version = version_q.search(data)
    if version:
        result["pkg_ver"] = version
    else:
        latest_q: jmespath.parser.ParsedResult = queries["latest"]
        latest = latest_q.search(data)
        result["pkg_ver"] = latest
        data = jmespath.search(queries["versions"].format(latest), data)
    result["pkg_lic"] = license_q.search(data) or ["Other"]
    dep_data = dependencies_q.search(data)
    if dep_data:
        result["pkg_dep"] = [";".join(tup) for tup in dep_data.items()]
    repo = repo_q.search(data) or ""
    return repo


def handle_rust(
    api_response: requests.Response, queries: dict, result: Result, url: str
):
    """
    Take api response and return required results object
    :param api_response: response from requests get
    :param queries: compiled jmespath queries
    :param result: object to mutate
    :param url: url queried for response
    """
    dep_url = url + "/dependencies"
    dep_res = requests.get(dep_url)
    version_q: jmespath.parser.ParsedResult = queries["version"]
    license_q: jmespath.parser.ParsedResult = queries["license"]
    dependencies_q: jmespath.parser.ParsedResult = queries["dependency"]
    if api_response.status_code == 404 or dep_res.status_code == 404:
        return ""
    data = api_response.json()
    dep = dep_res.json()
    result["pkg_ver"] = version_q.search(data) or ""
    result["pkg_lic"] = [license_q.search(data) or "Other"]
    req_file_data = dependencies_q.search(dep) or []
    result["pkg_dep"] = req_file_data


def scrape_go(response: requests.Response, queries: dict, result: Result, url: str):
    """
    Take api response and return required results object
    :param response: response from requests get
    :param queries: compiled jmespath queries
    :param result: object to mutate
    :param url: go url scraped
    """
    soup = BeautifulSoup(response.text, "html.parser")
    name_parse = queries["name"].split(".")
    name_data = (
        soup.find(name_parse[0], class_=name_parse[1]).getText().strip().split(" ")
    )
    package_name = result["pkg_name"]
    if len(name_data) > 1:
        package_name = name_data[-1].strip()
    key_parse = queries["parse"].split(".")
    dep_parse = queries["dependencies"].split(".")
    key_element = soup.find(key_parse[0], class_=key_parse[1]).getText()
    key_data = re.findall(r"([^ \n:]+): ([- ,.\w]+)", key_element)
    data = dict(key_data)
    dependencies_tag = []
    dep_res = requests.get(url + "?tab=imports", allow_redirects=False)
    if dep_res.status_code == 200:
        dep_soup = BeautifulSoup(dep_res.text, "html.parser")
        dependencies_tag = [
            dependency.getText().strip()
            for dependency in dep_soup.findAll(dep_parse[0], class_=dep_parse[1])
        ]
    result["pkg_name"] = package_name
    result["pkg_ver"] = data[queries["version"]] or ""
    result["pkg_lic"] = [data[queries["license"]] or "Other"]
    result["pkg_dep"] = dependencies_tag


def go_versions(url: str, queries: dict) -> list:
    """
    Get list of all versions for go package
    :param queries: compiled jmespath queries
    :param url: go url scraped
    :return: list of versions
    """
    ver_parse = queries["versions"].split(".")
    ver_res = requests.get(url + "?tab=versions", allow_redirects=False)
    releases = []
    if ver_res.status_code == 200:
        version_soup = BeautifulSoup(ver_res.text, "html.parser")
        releases = [
            release.getText().strip()
            for release in version_soup.findAll(ver_parse[0], class_=ver_parse[1])
        ]
    return releases


def rust_versions(api_response: requests.Response, queries: dict) -> list:
    """
    Get list of all versions for rust package
    :param queries: compiled jmespath queries
    :param api_response: registry response
    :return: list of versions
    """
    if api_response.status_code == 404:
        return []
    data = api_response.json()
    versions_q: jmespath.parser.ParsedResult = queries["versions"]
    versions = versions_q.search(data)
    if not versions:
        return []
    return versions


def js_versions(api_response: requests.Response, queries: dict) -> list:
    """
    Get list of all versions for js package
    :param queries: compiled jmespath queries
    :param api_response: registry response
    :return: list of versions
    """
    if api_response.status_code == 404:
        return []
    data = api_response.json()
    versions_q: jmespath.parser.ParsedResult = queries["versions"]
    versions = versions_q.search(data)
    if not versions:
        return []
    return versions


def py_versions(api_response: requests.Response, queries: dict) -> list:
    """
    Get list of all versions for py package
    :param queries: compiled jmespath queries
    :param api_response: registry response
    :return: list of versions
    """
    if api_response.status_code == 404:
        return []
    data = api_response.json()
    versions_q: jmespath.parser.ParsedResult = queries["versions"]
    versions = versions_q.search(data)
    if not versions:
        return []
    return versions
