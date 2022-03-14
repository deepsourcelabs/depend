"""License & Version Extractor"""

import constants
import tldextract
import requests
from datetime import datetime, timedelta
import logging
from typing import List, Optional
import re

from vcs.github_worker import handle_github
from helper import Result, handle_pypi, handle_npmjs, scrape_go, parse_dep_response
from helper import go_versions, js_versions, py_versions
from error import LanguageNotSupportedError, VCSNotSupportedError
from constants import REGISTRY


def handle_vcs(
        language: str,
        dependency: str,
        result: Result,
        gh_token: str = "",
):
    """
    Fall through to VCS check for a go namespace (only due to go.mod check)
    :param language: primary language of the package
    :param gh_token: auth token for vcs requests
    :param dependency: package not found in other repositories
    :param result: object with name version license and dependencies
    """
    if "github.com" in dependency:
        handle_github(language, dependency, result, gh_token)
    else:
        raise VCSNotSupportedError(dependency)


def make_url(
        language: str,
        package: str,
        version: str = ""
) -> str:
    """
    Construct the API JSON request URL or web URL to scrape
    :param language: lowercase: python, javascript or go
    :param package: as imported in source
    :param version: optional version specification
    :return: url to fetch
    """
    match language:
        case "python":
            if version:
                url_elements = (REGISTRY[language]['url'], package, version, 'json')
            else:
                url_elements = (REGISTRY[language]['url'], package, 'json')
        case "javascript":
            if version:
                url_elements = (REGISTRY[language]['url'], package, version)
            else:
                url_elements = (REGISTRY[language]['url'], package)
        case "go":
            if version:
                url_elements = (REGISTRY[language]['url'], package + "@" + version)
            else:
                url_elements = (REGISTRY[language]['url'], package)
        case _:
            raise LanguageNotSupportedError(language)
    return "/".join(url_elements).rstrip("/")


def find_github(text: str) -> str:
    """
    Returns a repo url from a string
    :param text: string to check
    """
    repo_identifier = re.search(
        r"github.com/([^/]+)/([^/.\r\n]+)(?:/tree/|)?([^/.\r\n]+)?",
        text
    )
    if repo_identifier:
        return "https://github.com/" + \
               repo_identifier.group(1) + "/" + repo_identifier.group(2)
    else:
        return ""


def make_single_request(
        es: any,
        language: str,
        package: str,
        version: str = "",
        gh_token: Optional[str] = None
) -> dict:
    """
    Obtain package license and dependency information.
    :param es: ElasticSearch Instance
    :param language: python, javascript or go
    :param package: as imported
    :param version: check for specific version
    :param gh_token: GitHub token for authentication
    :return: result object with name version license and dependencies
    """
    result_list = []
    package_version = package
    if es is not None:
        ESresult: dict = es.get(index=language, id=package_version, ignore=404)
        if ESresult.get("found"):
            db_time = datetime.fromisoformat(
                ESresult["_source"]["timestamp"],
            )
            if db_time - datetime.utcnow() < timedelta(
                    seconds=constants.CACHE_EXPIRY
            ):
                logging.info("Using " + package + " found in ES Database")
                return ESresult["_source"]

    if not version:
        vers = []
        url = make_url(language, package, version)
        response = requests.get(url)
        queries = REGISTRY[language]
        match language:
            case "python":
                vers = py_versions(response, queries)
            case "javascript":
                vers = js_versions(response, queries)
            case "go":
                vers = go_versions(url, queries)
    else:
        vers = [version]

    for ver in vers:
        url = make_url(language, package, ver)
        logging.info(url)
        response = requests.get(url)
        queries = REGISTRY[language]

        result: Result = {
            'import_name': '',
            'lang_ver': '',
            'pkg_name': package,
            'pkg_ver': '',
            'pkg_lic': '',
            'pkg_err': {},
            'pkg_dep': [],
            'timestamp': datetime.utcnow().isoformat()
        }
        repo = ""
        match language:
            case "python":
                repo = handle_pypi(response, queries, result)
            case "javascript":
                repo = handle_npmjs(response, queries, result)
            case "go":
                if response.status_code == 200:
                    # Handle 302: Redirection
                    if response.history:
                        red_url = response.url + "@" + version
                        response = requests.get(red_url)
                    scrape_go(response, queries, result, url)
                else:
                    repo = package
        supported_domains = [
            "github",
        ]
        if repo:
            if tldextract.extract(repo).domain not in supported_domains:
                repo = find_github(response.text)
            if repo:
                handle_vcs(language, repo, result, gh_token)
        if es is not None:
            es.index(
                index=language,
                id=package_version,
                document=result
            )
        # handle vers into format
        # parse_dep_response
        result_list.append(result)
    return parse_dep_response(result_list)


def make_multiple_requests(
        es: any,
        language: str,
        packages: List[str],
        gh_token: Optional[str] = None
) -> list:
    """
    Obtain license and dependency information for list of packages.
    :param es: ElasticSearch Instance
    :param language: python, javascript or go
    :param packages: a list of dependencies in each language
    :param gh_token: GitHub token for authentication
    :return: result object with name version license and dependencies
    """
    result = []

    for package in packages:
        name_ver = package.replace("@", ";").split(";")
        if len(name_ver) == 1:
            dep_resp = make_single_request(es, language, package, gh_token=gh_token)
        else:
            dep_resp = make_single_request(
                es, language, name_ver[0], name_ver[1], gh_token
            )
        result.append(dep_resp)
    return result
