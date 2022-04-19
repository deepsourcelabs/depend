"""License & Version Extractor"""
import logging
from datetime import datetime, timedelta
from typing import List, Optional

import requests
import requests_cache

import constants
from error import LanguageNotSupportedError, VCSNotSupportedError
from helper import Result, handle_npmjs, handle_pypi, scrape_go
from vcs.github_worker import handle_github

requests_cache.install_cache('test_cache', expire_after=constants.CACHE_EXPIRY)
source: dict = constants.REGISTRY


def handle_vcs(
        dependency: str,
        result: Result,
        gh_token: str = None,
):
    """
    Fall through to VCS check for a go namespace (only due to go.mod check)
    :param gh_token: auth token for vcs requests
    :param dependency: package not found in other repositories
    :param result: object with name version license and dependencies
    """
    if "github.com" in dependency:
        handle_github(dependency, result, gh_token)
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
                url_elements = (source[language]['url'], package, version, 'json')
            else:
                url_elements = (source[language]['url'], package, 'json')
        case "javascript":
            if version:
                url_elements = (source[language]['url'], package, version)
            else:
                url_elements = (source[language]['url'], package)
        case "go":
            if version:
                url_elements = (source[language]['url'], package + "@" + version)
            else:
                url_elements = (source[language]['url'], package)
        case _:
            raise LanguageNotSupportedError(language)
    return "/".join(url_elements).rstrip("/")


def make_single_request(
        es: any,
        language: str,
        package: str,
        version: str = "",
        gh_token: Optional[str] = None
) -> Result:
    """
    Obtain package license and dependency information.
    :param es: ElasticSearch Instance
    :param language: python, javascript or go
    :param package: as imported
    :param version: check for specific version
    :param gh_token: GitHub token for authentication
    :return: result object with name version license and dependencies
    """
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

    url = make_url(language, package, version)
    logging.info(url)
    response = requests.get(url)
    queries = source[language]

    result: Result = {
        'name': package,
        'version': '',
        'license': '',
        'dependencies': [],
        'timestamp': datetime.utcnow().isoformat()
    }

    match language:
        case "python":
            handle_pypi(response, queries, result)
        case "javascript":
            handle_npmjs(response, queries, result)
        case "go":
            if response.status_code == 200:
                # Handle 302: Redirection
                if response.history:
                    red_url = response.url + "@" + version
                    response = requests.get(red_url)
                scrape_go(response, queries, result, url)
            else:
                handle_vcs(package, result, gh_token)
    if es is not None:
        es.index(
            index=language,
            id=package_version,
            document=result
        )
    return result


def make_multiple_requests(
        es: any,
        language: str,
        packages: List[str],
        gh_token: Optional[str] = None
) -> dict:
    """
    Obtain license and dependency information for list of packages.
    :param es: ElasticSearch Instance
    :param language: python, javascript or go
    :param packages: a list of dependencies in each language
    :param gh_token: GitHub token for authentication
    :return: result object with name version license and dependencies
    """
    result = {}

    for package in packages:
        name_ver = package.split("@")
        if len(name_ver) == 1:
            result[package] = make_single_request(es, language, package)
        else:
            result[package] = make_single_request(
                es, language, name_ver[0], name_ver[1], gh_token
            )
    return result
