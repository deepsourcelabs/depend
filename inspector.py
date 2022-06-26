"""License & Version Extractor"""

import logging
import re
import time
from datetime import datetime
from typing import Any, List, Tuple

import requests
from tldextract import extract

from constants import CACHE_EXPIRY, REGISTRY
from db.postgres_worker import add_data, get_data, upd_data
from dep_types import Result
from dependencies.helper import (
    go_versions,
    handle_npmjs,
    handle_pypi,
    handle_rust,
    js_versions,
    parse_dep_response,
    py_versions,
    rust_versions,
    scrape_go,
)
from error import LanguageNotSupportedError, VCSNotSupportedError
from vcs.github_worker import handle_github


def handle_vcs(
    language: str,
    dependency: str,
    result: Result,
) -> None:
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


def make_url(language: str, package: str, version: str = "") -> str:
    """
    Construct the API JSON request URL or web URL to scrape
    :param language: lowercase: python, javascript or go
    :param package: as imported in source
    :param version: optional version specification
    :return: url to fetch
    """
    url_elements: Tuple[str, ...]
    match language:
        case "python":
            if version:
                url_elements = (
                    str(REGISTRY[language]["url"]),
                    package,
                    version,
                    "json",
                )
            else:
                url_elements = (str(REGISTRY[language]["url"]), package, "json")
        case "javascript":
            if version:
                url_elements = (str(REGISTRY[language]["url"]), package, version)
            else:
                url_elements = (str(REGISTRY[language]["url"]), package)
        case "go":
            if version:
                url_elements = (str(REGISTRY[language]["url"]), package + "@" + version)
            else:
                url_elements = (str(REGISTRY[language]["url"]), package)
        case "rust":
            if version:
                url_elements = (REGISTRY[language]["url"], package, version)
            else:
                url_elements = (REGISTRY[language]["url"], package, "versions")
        case _:
            raise LanguageNotSupportedError(language)
    return "/".join(url_elements).rstrip("/")


def find_github(text: str) -> str:
    """
    Returns a repo url from a string
    :param text: string to check
    """
    repo_identifier = re.search(
        r"github.com/([^/]+)/([^/.\r\n]+)(?:/tree/|)?([^/.\r\n]+)?", text
    )
    if repo_identifier:
        return (
            "https://github.com/"
            + repo_identifier.group(1)
            + "/"
            + repo_identifier.group(2)
        )
    else:
        return ""


def make_single_request(
    psql: Any,
    language: str,
    package: str,
    version: str = "",
    force_schema: bool = True,
) -> dict | Result | List[Result]:
    """
    Obtain package license and dependency information.
    :param psql: Postgres connection
    :param language: python, javascript or go
    :param package: as imported
    :param version: check for specific version
    :param force_schema: returns schema compliant response if true
    :return: result object with name version license and dependencies
    """
    result_list = []
    result: Result = {
        "import_name": "",
        "lang_ver": [],
        "pkg_name": package,
        "pkg_ver": "",
        "pkg_lic": ["Other"],
        "pkg_err": {},
        "pkg_dep": [],
        "timestamp": datetime.utcnow().isoformat(),
    }
    if not version:
        vers = []
        url = make_url(language, package, version)
        queries = REGISTRY[language]
        match language:
            case "python":
                response = requests.get(url)
                vers = py_versions(response, queries)
            case "javascript":
                response = requests.get(url)
                vers = js_versions(response, queries)
            case "go":
                vers = go_versions(url, queries)
            case "rust":
                response = requests.get(url)
                vers = rust_versions(response, queries)
    else:
        vers = [version]
    if not vers:
        vers = [""]
    for ver in vers:
        if psql:
            db_data = get_data(psql, language, package, ver)
            if db_data:
                db_time: datetime = db_data.timestamp
                if (
                    time.mktime(db_time.timetuple())
                    - time.mktime(datetime.utcnow().timetuple())
                    < CACHE_EXPIRY
                ):
                    logging.info("Using " + package + " found in Postgres Database")
                    return db_data
        if "||" in version:
            git_url, git_branch = version.split("||")
            handle_vcs(language, git_url + "/tree/" + git_branch, result)
        else:
            url = make_url(language, package, ver)
            logging.info(url)
            response = requests.get(url)
            queries = REGISTRY[language]
            repo = ""
            match language:
                case "python":
                    repo = handle_pypi(response, queries, result)
                case "javascript":
                    repo = handle_npmjs(response, queries, result)
                case "rust":
                    handle_rust(response, queries, result, url)
                case "go":
                    if response.status_code == 200:
                        # Handle 302: Redirection
                        red_url = url
                        if response.history:
                            red_url = response.url + "@" + version
                            response = requests.get(red_url)
                        scrape_go(response, queries, result, red_url)
                    else:
                        repo = package
            supported_domains = [
                "github.com",
            ]
            if repo:
                c_domain = extract(str(repo)).domain + "." + extract(str(repo)).suffix
                if c_domain not in supported_domains or extract(str(repo)).subdomain:
                    repo = find_github(response.text)
                if repo:
                    handle_vcs(language, repo, result)
        if psql:
            db_data = get_data(psql, language, package, ver)
            if not db_data:
                add_data(
                    psql,
                    language,
                    package,
                    ver,
                    result.get("import_name", ""),
                    result.get("lang_ver", []),
                    result.get("pkg_lic", []),
                    result.get("pkg_err", {}),
                    result.get("pkg_dep", []),
                )
            else:
                upd_data(
                    psql,
                    language,
                    package,
                    ver,
                    result.get("import_name", ""),
                    result.get("lang_ver", []),
                    result.get("pkg_lic", []),
                    result.get("pkg_err", {}),
                    result.get("pkg_dep", []),
                )
        result_list.append(result)
    if force_schema:
        return parse_dep_response(result_list)
    else:
        return result_list


def make_multiple_requests(
    psql: Any,
    language: str,
    packages: List[str],
) -> List[Any]:
    """
    Obtain license and dependency information for list of packages.
    :param psql: Postgres connection
    :param language: python, javascript or go
    :param packages: a list of dependencies in each language
    :return: result object with name version license and dependencies
    """
    result = []
    for package in packages:
        name_ver = (package[0] + package[1:].replace("@", ";")).rsplit(";", 1)
        if len(name_ver) == 1:
            dep_resp = make_single_request(psql, language, package)
        else:
            dep_resp = make_single_request(psql, language, name_ver[0], name_ver[1])
        result.append(dep_resp)
    return result
