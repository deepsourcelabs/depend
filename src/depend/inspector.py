"""License & Version Extractor"""
import logging
import re
from datetime import datetime
from typing import Any, List, Optional, Set, Tuple

from requests import Response

from depend.constants import REGISTRY
from depend.dep_helper import requests
from depend.dependencies.dep_types import Result
from depend.dependencies.helper import (
    fix_constraint,
    go_versions,
    handle_cs,
    handle_npmjs,
    handle_php,
    handle_pypi,
    handle_rust,
    js_versions,
    nuget_versions,
    parse_dep_response,
    php_versions,
    py_versions,
    resolve_version,
    rust_versions,
    scrape_go,
)
from depend.error import LanguageNotSupportedError, VCSNotSupportedError
from depend.vcs.github_worker import handle_github


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
    suffix = ""
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
        case "cs":
            # Repository expects package name to be lowercase for it to work reliably
            package = package.lower()
            if version:
                url_elements = (
                    REGISTRY[language]["url"],
                    package,
                    version,
                    package + ".nuspec",
                )
            else:
                url_elements = (REGISTRY[language]["url"], package, "index.json")
        case "php":
            url_elements = (REGISTRY[language]["url"], package)
            suffix = ".json"
        case "rust":
            if version:
                url_elements = (REGISTRY[language]["url"], package, version)
            else:
                url_elements = (REGISTRY[language]["url"], package, "versions")
        case _:
            raise LanguageNotSupportedError(language)
    return "/".join(url_elements).rstrip("/") + suffix


def find_github(text: str) -> str:
    """
    Returns a repo url from a string
    :param text: string to check
    """
    repo_identifier = re.search(
        r"github.com/([^/]+)/([^/.\r\n]+)(?:/tree/|)?([^/.,\s\r\n]+)?", text
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
    language: str,
    package: str,
    version: str = "",
    force_schema: bool = True,
    all_ver: bool = False,
) -> Tuple[dict | Result | List[Result], Set[str]]:
    """
    Obtain package license and dependency information.
    :param language: python, javascript or go
    :param package: as imported
    :param version: check for specific version
    :param force_schema: returns schema compliant response if true
    :param all_ver: all versions queried if version not supplied
    :return: result object with name version license and dependencies
    """
    rem_dep: Set[str] = set()
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
    repo = ""
    vers = []
    response: Response
    supported_domains = [
        "github.com",
    ]
    # Single request is meant to be handled by VCS provider
    if any(domain in version for domain in supported_domains):
        if "||" in version:
            git_url, git_branch = version.split("||")
            repo = git_url + "/tree/" + git_branch
        else:
            repo = version
        vers = [repo]
    # Requested for a version using a version constraint
    else:
        version_constraints = fix_constraint(language, version)
        url = make_url(language, package)
        queries = REGISTRY[language]
        # Get all available versions for specified package
        response = requests.get(url)
        red_url = url
        match language:
            case "python":
                vers = py_versions(response, queries)
            case "javascript":
                vers = js_versions(response, queries)
            case "go":
                if response.status_code == 200:
                    # Handle 302: Redirection
                    if response.history:
                        red_url = response.url
                vers = go_versions(red_url, queries)
            case "cs":
                vers = nuget_versions(response, queries)
            case "php":
                vers = php_versions(response, queries)
            case "rust":
                vers = rust_versions(response, queries)
        # Parse only one version resolved from constraint provided
        logging.debug(vers)
        if not all_ver and vers:
            resolved_version = resolve_version(vers, version_constraints)
            if resolved_version is not None:
                vers = [resolved_version]
            else:
                vers = []
                logging.warning(
                    f"No version could be resolved for package {package} with version constraint {version}"
                )
    # Check multiple versions of specified package
    for ver in vers:
        # Construct URL for version specific data
        url = make_url(language, package, ver)
        logging.info(url)
        response = requests.get(url)
        queries = REGISTRY[language]
        # Collect repo if available to do vcs query if data incomplete
        match language:
            case "python":
                repo = handle_pypi(response, queries, result)
            case "javascript":
                repo = handle_npmjs(response, queries, result)
            case "cs":
                repo = handle_cs(response, queries, result)
            case "php":
                handle_php(response, queries, result, ver)
            case "rust":
                handle_rust(response, queries, result, url)
            case "go":
                if response.status_code == 200:
                    red_url = url
                    if response.history:
                        red_url = response.url + "@" + version
                        response = requests.get(red_url)
                    scrape_go(response, queries, result, red_url)
                elif not repo:
                    repo = package
        if repo:
            try:
                handle_vcs(language, repo, result)
            except VCSNotSupportedError:
                logging.info(f"Unable to use VCS as unsupported: {repo}")
        else:
            if response.status_code != 200:
                logging.error(
                    f"{response.status_code}: {url} maybe git: {find_github(response.text)}"
                )
        rem_dep = set(result.get("pkg_dep") or [])
        result_list.append(result)
    if not result_list:
        result_list = [result]
    if force_schema:
        return parse_dep_response(result_list), rem_dep
    else:
        return result_list, rem_dep


def make_multiple_requests(
    language: str,
    packages: List[str],
    depth: Optional[int] = None,
    result: Optional[list] = None,
) -> List[Any]:
    """
    Obtain license and dependency information for list of packages.
    :param language: python, javascript or go
    :param packages: a list of dependencies in each language
    :param depth: depth of recursion, None for no limit and 0 for input parsing alone
    :param result: optional result object to append to during recursion
    :return: result object with name version license and dependencies
    """
    return _make_multiple_requests(
        language,
        packages,
        depth,
        result,
        _already_queried=set(),
    )


def _make_multiple_requests(
    language: str,
    packages: List[str],
    depth: Optional[int] = None,
    result: Optional[list] = None,
    _already_queried: Optional[Set] = None,
) -> List[Any]:
    """
    Recursive implementation of make_multiple_requests, with caching.
    :param _already_queried: set that keeps track of queried packages
    """
    logging.debug("Fetching packages: %s", packages)
    if result is None:
        result = []
    deps = set()
    for package_d in packages:
        name_ver = package_d.rsplit(";", 1)
        if len(name_ver) == 1:
            dep_resp, res_deps = make_single_request(language, name_ver[0])
        else:
            dep_resp, res_deps = make_single_request(language, name_ver[0], name_ver[1])
        result.append(dep_resp)
        deps = deps.union(res_deps)
        _already_queried.add(package_d)
    deps.difference_update(_already_queried)
    # higher levels may ignore version specifications
    if len(deps) == 0:
        return result
    if depth is None:
        return _make_multiple_requests(
            language, list(deps), result=result, _already_queried=_already_queried
        )
    elif isinstance(depth, int) and depth > 0:
        return _make_multiple_requests(
            language, list(deps), depth - 1, result, _already_queried
        )
    else:
        return result
