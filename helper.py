"""Helper Functions for Inspector."""
import logging
import re
from typing import TypedDict, List
import requests
import jmespath
from bs4 import BeautifulSoup
from pkg_resources import parse_requirements


class Result(TypedDict):
    """Type hinting for results"""

    name: str
    version: str
    license: str
    dependencies: List[List[str]]
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


def handle_requirements_txt(req_file_data: str) -> list:
    """
    Parse requirements file
    :param req_file_data: Content of requirements.txt
    :return: list of requirement and specs
    """
    install_reqs = parse_requirements(req_file_data)
    # not considering extras i.e. requests[security] == 2.9.1
    return [
        [ir.key, ir.specs]
        for ir in install_reqs
    ]


def handle_go_mod(req_file_data: str) -> list:
    """
    Parse go.mod file
    :param req_file_data: Content of go.mod
    :return: list of requirement and specs
    """
    return re.findall(
        r"[\s/]+[\"|\']?([^\s\n(\"\']+)[\"|\']?\s+[\"|\']?v([^\s\n]+)[\"|\']?",
        req_file_data
    )


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
