"""Helper Functions for Inspector."""
import re
from typing import TypedDict, Optional

import jmespath
import requests
from bs4 import BeautifulSoup

from dependencies.go import go_worker
from dependencies.js import js_worker
from dependencies.py import py_worker
from error import FileNotSupportedError


class Result(TypedDict):
    """Type hinting for results"""
    import_name: Optional[str]
    lang_ver: str
    pkg_name: str
    pkg_ver: str
    pkg_lic: str
    pkg_err: str
    pkg_dep: list
    timestamp: str


def parse_license(license_file: str, license_dict: dict) -> str:
    """
    Check license file content and return the possible license type.
    :param license_file: String containing license file content
    :param license_dict: Dictionary mapping license files and unique substring
    :return: Detected license type as a String, `Other` if failed to detect
    """
    licenses = [
        license_str for lic, license_str
        in license_dict.items() if lic in license_file
    ]
    return ";".join(licenses) or "Other"


def handle_dep_file(
        file_name: str,
        file_content: str,
        gh_token: str
) -> dict:
    """
    Parses contents of requirement file and returns useful insights
    :param gh_token: GitHub token
    :param file_name: name of requirement file
    :param file_content: content of the file
    :return: key features for dependency-inspector
    """
    file_extension = file_name.split(".")[-1]
    match file_extension:
        case 'mod':
            return go_worker.handle_go_mod(file_content)
        case 'json':
            return js_worker.handle_json(file_content)
        case 'lock':
            return js_worker.handle_yarn_lock(file_content)
        case 'txt':
            return py_worker.handle_requirements_txt(file_content)
        case 'toml':
            return py_worker.handle_toml(file_content)
        case 'py':
            return py_worker.handle_setup_py(file_content, gh_token)
        case 'cfg':
            return py_worker.handle_setup_cfg(file_content)
        case _:
            raise FileNotSupportedError(file_name)


def parse_dep_response(
        ecs: list[dict],
) -> dict:
    """
    Constructs required schema from extracted fields
    :param ecs: list of extracted content to fix
    :return: final result for a package as per schema
    """
    final_response = {
        ecs[0].get("pkg_name"): {
            "versions": {
                ec.get("pkg_ver"): {
                    "import_name": ec.get("import_name", ""),
                    "lang_ver": ec.get("lang_ver"),
                    "pkg_lic": ec.get("pkg_lic"),
                    "pkg_err": ec.get("pkg_err"),
                    "pkg_dep": ec.get("pkg_dep"),
                    'timestamp': ec.get("timestamp")
                } for ec in ecs
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
    version_q: jmespath.parser.ParsedResult = queries['version']
    license_q: jmespath.parser.ParsedResult = queries['license']
    dependencies_q: jmespath.parser.ParsedResult = queries['dependency']
    repo_q: jmespath.parser.ParsedResult = queries['repo']
    data = api_response.json()
    result['pkg_ver'] = version_q.search(data)
    result['pkg_lic'] = license_q.search(data)
    req_file_data = "\n".join(dependencies_q.search(data) or "")
    result['pkg_dep'] = py_worker.handle_requirements_txt(
        req_file_data
    ).get("pkg_dep")
    repo = repo_q.search(data) or ""
    return repo


def handle_npmjs(api_response: requests.Response, queries: dict, result: Result):
    """
    Take api response and return required results object
    :param api_response: response from requests get
    :param queries: compiled jmespath queries
    :param result: object to mutate
    """
    data = api_response.json()
    version_q: jmespath.parser.ParsedResult = queries['version']
    license_q: jmespath.parser.ParsedResult = queries['license']
    dependencies_q: jmespath.parser.ParsedResult = queries['dependency']
    repo_q: jmespath.parser.ParsedResult = queries['repo']
    version = version_q.search(data)
    if version is not None:
        result['pkg_ver'] = version
    else:
        latest_q: jmespath.parser.ParsedResult = queries['latest']
        latest = latest_q.search(data)
        result['pkg_ver'] = latest
        data = jmespath.search(
            queries['versions'].format(latest),
            data
        )
    result['pkg_lic'] = ";".join(license_q.search(data) or "")
    result['pkg_dep'] = list(
        map(
            list, dependencies_q.search(data).items()
        )
    )
    repo = repo_q.search(data) or ""
    return repo


def scrape_go(response: requests.Response, queries: dict, result: Result, url: str):
    """
    Take api response and return required results object
    :param response: response from requests get
    :param queries: compiled jmespath queries
    :param result: object to mutate
    :param url: go url scraped
    """
    soup = BeautifulSoup(response.text, "html.parser")
    name_parse = queries['name'].split('.')
    name_data = soup.find(
        name_parse[0],
        class_=name_parse[1]
    ).getText().strip().split(" ")
    package_name = result['pkg_name']
    if len(name_data) > 1:
        package_name = name_data[-1].strip()
    key_parse = queries['parse'].split('.')
    dep_parse = queries['dependencies'].split('.')
    key_element = soup.find(
        key_parse[0],
        class_=key_parse[1]
    ).getText()
    key_data = re.findall(r"([^ \n:]+): ([- ,.\w]+)", key_element)
    data = dict(key_data)
    dep_res = requests.get(url + "?tab=imports", allow_redirects=False)
    dependencies_tag = []
    if dep_res.status_code == 200:
        dep_soup = BeautifulSoup(dep_res.text, "html.parser")
        dependencies_tag = [
            [dependency.getText().strip()]
            for dependency in dep_soup.findAll(
                dep_parse[0],
                class_=dep_parse[1]
            )
        ]
    result['pkg_name'] = package_name
    result['pkg_ver'] = data[queries['version']]
    result['pkg_lic'] = data[queries['license']]
    result['pkg_dep'] = dependencies_tag


def go_versions(url: str, queries: dict) -> list:
    """
    Get list of all versions for go package
    :param queries: compiled jmespath queries
    :param url: go url scraped
    :return: list of versions
    """
    ver_parse = queries['versions'].split('.')
    ver_res = requests.get(url + "?tab=versions", allow_redirects=False)
    releases = []
    if ver_res.status_code == 200:
        version_soup = BeautifulSoup(ver_res.text, "html.parser")
        releases = [
            release.getText().strip()
            for release in version_soup.findAll(
                ver_parse[0],
                class_=ver_parse[1]
            )
        ]
    return releases


def js_versions(api_response: requests.Response, queries: dict) -> list:
    """
    Get list of all versions for js package
    :param queries: compiled jmespath queries
    :param api_response: registry response
    :return: list of versions
    """
    data = api_response.json()
    versions_q: jmespath.parser.ParsedResult = queries['repo']
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
    data = api_response.json()
    versions_q: jmespath.parser.ParsedResult = queries['repo']
    versions = versions_q.search(data)
    if not versions:
        return []
    return versions
