"""Helper Functions for Inspector."""
import json
import logging
import re
from ctypes import string_at
from typing import TypedDict, Collection

import jmespath
import requests
import yaml
from bs4 import BeautifulSoup
from pkg_resources import parse_requirements
from pyarn import lockfile

from error import FileNotSupportedError
from lib.lib_worker import getDepVer, free
from lib.setup_reader import LaxSetupReader


class Result(TypedDict):
    """Type hinting for results"""

    name: str
    version: str
    license: str
    dependencies: Collection
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


def handle_dep_file(file_name: str, file_content: str) -> Collection:
    """
    Parses contents of requirement file and returns useful insights
    :param file_name: name of requirement file
    :param file_content: content of the file
    :return: key features for dependency-inspector
    """
    match file_name:
        case 'go.mod':
            return handle_go_mod(file_content)
        case 'requirements.txt':
            return handle_requirements_txt(file_content)
        case 'package.json':
            return handle_package_json(file_content)
        case _:
            raise FileNotSupportedError(file_name)


def handle_requirements_txt(req_file_data: str) -> list:
    """
    Parse requirements file
    :param req_file_data: Content of requirements.txt
    :return: list of requirement and specs
    """
    install_reqs = parse_requirements(req_file_data)
    return [
        [ir.key, ir.specs]
        for ir in install_reqs
    ]


def handle_setup_py(req_file_data: str) -> dict:
    """
    Parse setup.cfg
    :param req_file_data: Content of setup.py
    :return: dict containing dependency info and specs
    """
    parser = LaxSetupReader()
    return parser.read_setup_py(req_file_data)


def get_setup_data(rough_data):
    """
    Iterates through string to match closing brace
    :param rough_data: setup function body
    :return: string to be analysed
    """
    stack = ["("]
    index = 0
    for index, i in enumerate(rough_data):
        if i == "(":
            stack.append(i)
        elif i == ")":
            if len(stack) > 0:
                stack.pop()
            else:
                break
        if len(stack) == 0:
            break
    return index


def handle_yarn_lock(req_file_data: str) -> list:
    """
    Parse yarn lock file
    :param req_file_data: Content of yarn.lock
    :return: list of requirement and specs
    """
    if "lockfile v1" in req_file_data:
        parsed_lockfile = lockfile.Lockfile.from_str(req_file_data)
        unfiltered_content = parsed_lockfile.to_json()
    else:
        unfiltered_content = yaml.safe_load(req_file_data)
    return unfiltered_content


def handle_package_json(req_file_data: str) -> dict:
    """
    Parse json file generated by npm or yarn
    :param req_file_data: Content of package.json
    :return: list of requirement and specs
    """
    package_data = json.loads(req_file_data)
    filter_keys = [
        "name", "version", "license", "dependencies",
        "engines", "os", "cpu"
    ]
    return {
        k: v for k, v in package_data.items()
        if k in filter_keys
    }


def handle_go_mod(req_file_data: str) -> dict:
    """
    Parse go.mod file
    :param req_file_data: Content of go.mod
    :return: list of requirement and specs
    """
    ptr = getDepVer(
        req_file_data.encode('utf-8')
    )
    out = string_at(ptr).decode('utf-8')
    free(ptr)
    return json.loads(out)


def handle_javascript(req_file_data: str) -> list:
    """
    Port of https://github.com/npm/read-package-json
    :param req_file_data:
    """
    return [req_file_data]


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
    data = api_response.json()
    result['version'] = version_q.search(data)
    result['license'] = license_q.search(data)
    req_file_data = "\n".join(dependencies_q.search(data))
    result['dependencies'] = handle_requirements_txt(req_file_data)
    return result


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
    version = version_q.search(data)
    if version is not None:
        result['version'] = version
    else:
        latest_q: jmespath.parser.ParsedResult = queries['latest']
        latest = latest_q.search(data)
        result['version'] = latest
        data = jmespath.search(
            queries['versions'].format(latest),
            data
        )
    result['license'] = ";".join(license_q.search(data))
    result['dependencies'] = list(
        map(
            list, dependencies_q.search(data).items()
        )
    )


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
    package_name = result['name']
    if len(name_data) > 1:
        package_name = name_data[-1].strip()
    key_parse = queries['parse'].split('.')
    ver_parse = queries['versions'].split('.')
    dep_parse = queries['dependencies'].split('.')
    key_element = soup.find(
        key_parse[0],
        class_=key_parse[1]
    ).getText()
    key_data = re.findall(r"([^ \n:]+): ([a-zA-Z0-9-_ ,.]+)", key_element)
    data = dict(key_data)
    ver_res = requests.get(url + "?tab=versions", allow_redirects=False)
    dep_res = requests.get(url + "?tab=imports", allow_redirects=False)
    if ver_res.status_code == 200:
        version_soup = BeautifulSoup(ver_res.text, "html.parser")
        releases = [
            release.getText().strip()
            for release in version_soup.findAll(
                ver_parse[0],
                class_=ver_parse[1]
            )
        ]
        logging.info(releases)
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
    result['name'] = package_name
    result['version'] = data[queries['version']]
    result['license'] = data[queries['license']]
    result['dependencies'] = dependencies_tag
