"""License & Version Extractor"""
import ast
import logging
import re
from datetime import datetime
from typing import Any, List, Optional, Set, Tuple

from tldextract import extract

from constants import REGISTRY
from dep_helper import requests
from dependencies.dep_types import Result
from dependencies.helper import (
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
    language: str,
    package: str,
    version: str = "",
    force_schema: bool = True,
    all_ver: bool = False,
    ver_spec=None,
) -> Tuple[dict | Result | List[Result], List[str]]:
    """
    Obtain package license and dependency information.
    :param language: python, javascript or go
    :param package: as imported
    :param version: check for specific version
    :param force_schema: returns schema compliant response if true
    :param all_ver: all versions queried if version not supplied
    :param ver_spec: version specifier used
    :return: result object with name version license and dependencies
    """
    rem_dep: Set[str] = set()
    if ver_spec is None:
        ver_spec = "latest"
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
            case "cs":
                response = requests.get(url)
                vers = nuget_versions(response, queries)
            case "php":
                response = requests.get(url)
                vers = php_versions(response, queries)
            case "rust":
                response = requests.get(url)
                vers = rust_versions(response, queries)
        if not all_ver and vers:
            version_constraints = fix_constraint(language, ver_spec)
            resolved_version = resolve_version(vers, version_constraints)
            if resolved_version is not None:
                vers = [resolved_version]
            else:
                vers = []
    else:
        vers = [version]
    if not vers:
        vers = [""]
        logging.warning(
            f"No version could be resolved for package {package} with version constraint {ver_spec}"
        )
    for ver in vers:
        repo = ""
        response = ""
        supported_domains = [
            "github.com",
        ]
        if any(domain in version for domain in supported_domains):
            if "||" in version:
                git_url, git_branch = version.split("||")
                repo = git_url + "/tree/" + git_branch
            else:
                repo = version
        else:
            url = make_url(language, package, ver)
            logging.info(url)
            response = requests.get(url)
            queries = REGISTRY[language]
            if response.status_code != 200:
                logging.error("{}: {}".format(response.status_code, url))
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
                        # Handle 302: Redirection
                        red_url = url
                        if response.history:
                            red_url = response.url + "@" + version
                            response = requests.get(red_url)
                        scrape_go(response, queries, result, red_url)
                    else:
                        repo = package
        if repo:
            c_domain = extract(str(repo)).domain + "." + extract(str(repo)).suffix
            if c_domain not in supported_domains or extract(str(repo)).subdomain:
                repo = find_github(response.text)
            if repo:
                handle_vcs(language, repo, result)
        for dep in result.get("pkg_dep", []):
            rem_dep.add(dep)
        result_list.append(result)
    if force_schema:
        return parse_dep_response(result_list), list(rem_dep)
    else:
        return result_list, list(rem_dep)


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
    :param result: optional result object to apend to during revursion
    :return: result object with name version license and dependencies
    """
    deps = []
    if result is None:
        result = []
    for package_d in packages:
        package, ver_spec, *_ = package_d.rsplit("|", 1) + [""]
        if not ver_spec:
            name_ver = (package[0] + package[1:].replace("@", ";")).rsplit(";", 1)
            if len(name_ver) == 1:
                dep_resp, deps = make_single_request(language, package)
            else:
                dep_resp, deps = make_single_request(language, name_ver[0], name_ver[1])
        else:
            dep_resp, deps = make_single_request(
                language, package, ver_spec=ver_spec
            )
        result.append(dep_resp)
    # higher levels may ignore version specifications
    if depth is None and deps:
        return make_multiple_requests(language, deps, result=result)
    elif isinstance(depth, int) and depth > 0:
        return make_multiple_requests(language, deps, depth - 1, result)
    else:
        return result
