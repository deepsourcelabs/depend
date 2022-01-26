"""Helper Functions for Inspector."""
import logging
import re
from typing import TypedDict, List
import requests
import jmespath
from bs4 import BeautifulSoup


class Result(TypedDict):
    """Type hinting for results"""

    name: str
    version: str
    license: str
    dependencies: List[str]
    timestamp: str


def parse_license(license_file: str, license_dict: dict) -> str:
    """
    Check license file content and return the possible license type.
    :param license_file: String containing license file content
    :param license_dict: Dictionary mapping license files and unique substring
    :return: Detected license type as a String, `Other` if failed to detect
    """
    for lic in license_dict:
        if lic in license_file:
            return license_dict[lic]
    return "Other"


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
    result['dependencies'] = dependencies_q.search(data)
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
    result['dependencies'] = dependencies_q.search(data)


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
            dependency.getText().strip()
            for dependency in dep_soup.findAll(
                dep_parse[0],
                class_=dep_parse[1]
            )
        ]
    result['name'] = package_name
    result['version'] = data[queries['version']]
    result['license'] = data[queries['license']]
    result['dependencies'] = dependencies_tag
