"""License & Version Extractor"""

import logging
import re
import time
from datetime import datetime
from typing import List, Dict

import requests
import tldextract

from constants import REGISTRY, CACHE_EXPIRY
from db.postgres_worker import add_data, get_data, upd_data
from error import LanguageNotSupportedError, VCSNotSupportedError
from helper import Result, handle_pypi, handle_npmjs, scrape_go, parse_dep_response
from helper import go_versions, js_versions, py_versions
from vcs.github_worker import handle_github


def handle_vcs(
        language: str,
        dependency: str,
        result: Result,
):
    """
    Fall through to VCS check for a go namespace (only due to go.mod check)
    :param language: primary language of the package
    :param dependency: package not found in other repositories
    :param result: object with name version license and dependencies
    """
    if "github.com" in dependency:
        handle_github(language, dependency, result)
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
        psql: any,
        db_name: str,
        language: str,
        package: str,
        version: str = "",
        force_schema: bool = True
) -> Dict | list[Result]:
    """
    Obtain package license and dependency information.
    :param psql: Postgres connection
    :param db_name: Postgres database to be used
    :param language: python, javascript or go
    :param package: as imported
    :param version: check for specific version
    :param force_schema: returns schema compliant response if true
    :return: result object with name version license and dependencies
    """
    result_list = []
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
    if not vers:
        vers = [""]
    for ver in vers:
        run_flag = "new"
        if psql:
            db_data = get_data(
                psql,
                db_name,
                language,
                package,
                ver
            )
            if db_data:
                run_flag = "update"
                db_time = datetime.strptime(
                    db_data.timestamp,
                    '%Y-%m-%d %H:%M:%S.%f'
                )
                if time.mktime(db_time.timetuple()) - \
                        time.mktime(datetime.utcnow().timetuple()) < CACHE_EXPIRY:
                    logging.info("Using " + package + " found in Postgres Database")
                    return db_data
        url = make_url(language, package, ver)
        logging.info(url)
        response = requests.get(url)
        queries = REGISTRY[language]

        result: Result = {
            'import_name': '',
            'lang_ver': [],
            'pkg_name': package,
            'pkg_ver': '',
            'pkg_lic': ["Other"],
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
            if tldextract.extract(str(repo)).domain not in supported_domains:
                repo = find_github(response.text)
            if repo:
                handle_vcs(language, repo, result)
        if psql:
            if run_flag == "new":
                add_data(
                    psql,
                    db_name,
                    language,
                    result.get("pkg_name"),
                    result.get("pkg_ver"),
                    result.get("import_name"),
                    result.get("lang_ver"),
                    result.get("pkg_lic"),
                    result.get("pkg_err"),
                    result.get("pkg_dep"),
                )
            else:
                upd_data(
                    psql,
                    db_name,
                    language,
                    result.get("pkg_name"),
                    result.get("pkg_ver"),
                    result.get("import_name"),
                    result.get("lang_ver"),
                    result.get("pkg_lic"),
                    result.get("pkg_err"),
                    result.get("pkg_dep"),
                )
        result_list.append(result)
    if force_schema:
        return parse_dep_response(result_list)
    else:
        return result_list


def make_multiple_requests(
        psql: any,
        db_name: str,
        language: str,
        packages: List[str],
) -> list:
    """
    Obtain license and dependency information for list of packages.
    :param psql: Postgres connection
    :param db_name: Postgres database to be used
    :param language: python, javascript or go
    :param packages: a list of dependencies in each language
    :return: result object with name version license and dependencies
    """
    result = []

    for package in packages:
        name_ver = (package[0]+package[1:].replace("@", ";")).rsplit(';', 1)
        if len(name_ver) == 1:
            dep_resp = make_single_request(
                psql, db_name, language, package
            )
        else:
            dep_resp = make_single_request(
                psql, db_name, language, name_ver[0], name_ver[1]
            )
        result.append(dep_resp)
    return result
