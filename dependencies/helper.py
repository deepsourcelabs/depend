"""Helper Functions for Inspector."""
import datetime
import logging
import re
from collections import defaultdict
from typing import List, Optional

import jmespath
import requests
import xmltodict
from bs4 import BeautifulSoup
from packaging.specifiers import SpecifierSet
from packaging.version import Version
from requests import Response

from dep_helper import Result, requests
from error import FileNotSupportedError

from .cs.cs_worker import findkeys, handle_nuspec
from .go.go_worker import handle_go_mod
from .js.js_worker import handle_json, handle_yarn_lock
from .php.php_worker import handle_composer_json
from .py.py_helper import handle_requirements_txt
from .py.py_worker import handle_otherpy, handle_setup_cfg, handle_setup_py, handle_toml
from .rust.rust_worker import handle_cargo_toml, handle_lock


def parse_license(license_file: str, license_dict: dict) -> List[str]:
    """
    Check license file content and return the possible license type.
    :param license_file: String containing license file content
    :param license_dict: Dictionary mapping license files and unique substring
    :return: Detected license type as a String, `Other` if failed to detect
    """
    licenses = [
        license_str for lic, license_str in license_dict.items() if lic in license_file
    ]
    return licenses or ["Other"]


def handle_dep_file(
    file_name: str,
    file_content: str,
) -> Result:
    """
    Parses contents of requirement file and returns useful insights
    :param file_name: name of requirement file
    :param file_content: content of the file
    :return: key features for murdock
    """
    file_extension = file_name.split(".")[-1]
    if file_name in ["conda.yml", "tox.ini", "Pipfile", "Pipfile.lock"]:
        return handle_otherpy(file_content, file_name)
    match file_extension:
        case "mod":
            return handle_go_mod(file_content)
        case "json":
            if file_name == "composer.json":
                return handle_composer_json(file_content)
            return handle_json(file_content)
        case ["conda.yml", "tox.ini", "Pipfile", "Pipfile.lock"]:
            return handle_otherpy(file_content, file_name)
        case "lock":
            if file_name == "Cargo.lock":
                return handle_lock(file_content)
            return handle_yarn_lock(file_content)
        case "txt":
            return handle_requirements_txt(file_content)
        case "toml":
            if file_name == "Cargo.toml":
                return handle_cargo_toml(file_content)
            return handle_toml(file_content)
        case "py":
            return handle_setup_py(file_content)
        case "cfg":
            return handle_setup_cfg(file_content)
        case "xml":
            return handle_nuspec(file_content)
        case _:
            raise FileNotSupportedError(file_name)


def parse_dep_response(
    ecs: list[Result],
) -> dict:
    """
    Constructs required schema from extracted fields
    :param ecs: list of extracted content to fix
    :return: final result for a package as per schema
    """
    main_key = ecs[0].get("pkg_name")
    final_response = {
        main_key: {
            "versions": {
                ec.get("pkg_ver"): {
                    "import_name": ec.get("import_name") or main_key,
                    "lang_ver": ec.get("lang_ver") or [],
                    "pkg_lic": [ec.get("pkg_lic")]
                    if isinstance(ec.get("pkg_lic"), str)
                    else ec.get("pkg_lic"),
                    "pkg_err": ec.get("pkg_err") or {},
                    "pkg_dep": ec.get("pkg_dep") or {},
                    "timestamp": ec.get("timestamp").strftime("%Y-%m-%dT%H:%M:%S.%f")
                    if isinstance(ec.get("timestamp"), datetime.datetime)
                    else ec.get("timestamp"),
                }
                for ec in ecs
            }
        }
    }
    return final_response


def handle_pypi(api_response: Response, queries: dict, result: Result):
    """
    Take api response and return required results object
    :param api_response: response from requests get
    :param queries: compiled jmespath queries
    :param result: object to mutate
    """
    version_q: jmespath.parser.ParsedResult = queries["version"]
    license_q: jmespath.parser.ParsedResult = queries["license"]
    dependencies_q: jmespath.parser.ParsedResult = queries["dependency"]
    repo_q: jmespath.parser.ParsedResult = queries["repo"]
    if api_response.status_code == 404:
        return ""
    data = api_response.json()
    result["pkg_ver"] = version_q.search(data) or ""
    result["pkg_lic"] = [license_q.search(data) or "Other"]
    req_file_data = "\n".join(dependencies_q.search(data) or "")
    result["pkg_dep"] = handle_requirements_txt(req_file_data).get("pkg_dep", {})
    repo = repo_q.search(data) or ""
    return repo


def handle_cs(api_response: Response, queries: dict, result: Result):
    """
    Take api response and return required results object
    :param api_response: response from requests get
    :param queries: compiled jmespath queries
    :param result: object to mutate
    """
    _ = queries
    if api_response.status_code == 404:
        return ""
    req_file_data = api_response.text
    root = xmltodict.parse(req_file_data).get("package", {}).get("metadata")
    result["pkg_name"] = root.get("id")
    result["pkg_ver"] = root.get("version")
    # ignores "file" type
    if root.get("license", {}).get("@type") == "expression":
        result["pkg_lic"] = [root.get("license", {}).get("#text")]
    pkg_dep = defaultdict(list)
    for gen_e in findkeys(root.get("dependencies"), "dependency"):
        if isinstance(gen_e, list):
            for dep_e in gen_e:
                pkg_dep[dep_e.get("@id")].append(dep_e.get("@version"))
        else:
            pkg_dep[gen_e.get("@id")].append(gen_e.get("@version"))

    result["pkg_dep"] = pkg_dep
    # @type = git
    return root.get("repository", {}).get("@url")


def handle_npmjs(api_response: Response, queries: dict, result: Result):
    """
    Take api response and return required results object
    :param api_response: response from requests get
    :param queries: compiled jmespath queries
    :param result: object to mutate
    """
    if api_response.status_code == 404:
        return ""
    data = api_response.json()
    version_q: jmespath.parser.ParsedResult = queries["version"]
    license_q: jmespath.parser.ParsedResult = queries["license"]
    dependencies_q: jmespath.parser.ParsedResult = queries["dependency"]
    repo_q: jmespath.parser.ParsedResult = queries["repo"]
    version = version_q.search(data)
    if version:
        result["pkg_ver"] = version
    else:
        latest_q: jmespath.parser.ParsedResult = queries["latest"]
        latest = latest_q.search(data)
        result["pkg_ver"] = latest
        data = jmespath.search(queries["versions"].format(latest), data)
    result["pkg_lic"] = license_q.search(data) or ["Other"]
    dep_data = dependencies_q.search(data)
    if dep_data:
        pkg_dep = defaultdict(list)
        for tup in dep_data.items():
            pkg_dep[tup[0]].append(tup[1])
        result["pkg_dep"] = pkg_dep
    repo = repo_q.search(data) or ""
    return repo


def handle_php(api_response: Response, queries: dict, result: Result, ver: str):
    """
    Take api response and return required results object
    :param api_response: response from requests get
    :param queries: compiled jmespath queries
    :param result: object to mutate
    :param ver: queried versions
    """
    data = api_response.json()
    result["pkg_ver"] = ver
    versions_q: jmespath.parser.ParsedResult = queries["ver_data"]
    versions = versions_q.search(data)
    ver_data = versions.get(ver, {})
    result["pkg_lic"] = ver_data.get(queries["license_key"], ["Other"])
    dep_data = ver_data.get(queries["dependency_key"], {})
    lang_ver = dep_data.pop("php", "")
    result["lang_ver"] = [lang_ver]
    pkg_dep = defaultdict(list)
    for k, v in dep_data.items():
        pkg_dep[k].append(v)
    result["pkg_dep"] = pkg_dep


def handle_rust(api_response: Response, queries: dict, result: Result, url: str):
    """
    Take api response and return required results object
    :param api_response: response from requests get
    :param queries: compiled jmespath queries
    :param result: object to mutate
    :param url: url queried for response
    """
    dep_url = url + "/dependencies"
    dep_res = requests.get(dep_url)
    version_q: jmespath.parser.ParsedResult = queries["version"]
    license_q: jmespath.parser.ParsedResult = queries["license"]
    dependencies_q: jmespath.parser.ParsedResult = queries["dependency"]
    if api_response.status_code == 404 or dep_res.status_code == 404:
        return ""
    data = api_response.json()
    dep = dep_res.json()
    result["pkg_ver"] = version_q.search(data) or ""
    result["pkg_lic"] = [license_q.search(data) or "Other"]
    req_file_data = dependencies_q.search(dep) or []
    pkg_dep = defaultdict(list)
    for k, v in req_file_data.split(";"):
        pkg_dep[k].append(v)
    result["pkg_dep"] = pkg_dep


def scrape_go(response: Response, queries: dict, result: Result, url: str):
    """
    Take api response and return required results object
    :param response: response from requests get
    :param queries: compiled jmespath queries
    :param result: object to mutate
    :param url: go url scraped
    """
    soup = BeautifulSoup(response.text, "html.parser")
    name_parse = queries["name"].split(".")
    name_data = (
        soup.find(name_parse[0], class_=name_parse[1]).getText().strip().split(" ")
    )
    package_name = result["pkg_name"]
    if len(name_data) > 1:
        package_name = name_data[-1].strip()
    key_parse = queries["parse"].split(".")
    dep_parse = queries["dependencies"].split(".")
    key_element = soup.find(key_parse[0], class_=key_parse[1]).getText()
    key_data = re.findall(r"([^ \n:]+): ([- ,.\w]+)", key_element)
    data = dict(key_data)
    pkg_dep = defaultdict(list)
    # requirements not version specific
    non_ver_url = url.split("@")[0] + "?tab=imports"
    dep_res = requests.get(non_ver_url, allow_redirects=False)
    if dep_res.status_code == 200:
        dep_soup = BeautifulSoup(dep_res.text, "html.parser")
        for dependency in dep_soup.findAll(dep_parse[0], class_=dep_parse[1]):
            pkg_dep[dependency.getText().strip()].append("latest")

    result["pkg_name"] = package_name
    result["pkg_ver"] = data[queries["version"]] or ""
    result["pkg_lic"] = [data[queries["license"]] or "Other"]
    result["pkg_dep"] = pkg_dep


def go_versions(url: str, queries: dict) -> list:
    """
    Get list of all versions for go package
    :param queries: compiled jmespath queries
    :param url: go url scraped
    :return: list of versions
    """
    ver_parse = queries["versions"].split(".")
    ver_res = requests.get(url + "?tab=versions", allow_redirects=False)
    releases = []
    if ver_res.status_code == 200:
        version_soup = BeautifulSoup(ver_res.text, "html.parser")
        releases = [
            release.getText().strip()
            for release in version_soup.findAll(ver_parse[0], class_=ver_parse[1])
        ]
    return releases


def rust_versions(api_response: Response, queries: dict) -> list:
    """
    Get list of all versions for rust package
    :param queries: compiled jmespath queries
    :param api_response: registry response
    :return: list of versions
    """
    if api_response.status_code == 404:
        return []
    data = api_response.json()
    versions_q: jmespath.parser.ParsedResult = queries["versions"]
    versions = versions_q.search(data)
    if not versions:
        return []
    return versions


def js_versions(api_response: Response, queries: dict) -> list:
    """
    Get list of all versions for js package
    :param queries: compiled jmespath queries
    :param api_response: registry response
    :return: list of versions
    """
    if api_response.status_code == 404:
        return []
    data = api_response.json()
    versions_q: jmespath.parser.ParsedResult = queries["versions"]
    versions = versions_q.search(data)
    if not versions:
        return []
    return versions


def py_versions(api_response: Response, queries: dict) -> list:
    """
    Get list of all versions for py package
    :param queries: compiled jmespath queries
    :param api_response: registry response
    :return: list of versions
    """
    if api_response.status_code == 404:
        return []
    data = api_response.json()
    versions_q: jmespath.parser.ParsedResult = queries["versions"]
    versions = versions_q.search(data)
    if not versions:
        return []
    return versions


def ruby_versions(api_response: Response, queries: dict) -> list:
    """
    Get list of all versions for ruby package
    :param queries: compiled jmespath queries
    :param api_response: registry response
    :return: list of versions
    """
    if api_response.status_code == 404:
        return []
    data = api_response.json()
    versions_q: jmespath.parser.ParsedResult = queries["version"]
    versions = versions_q.search(data)
    if not versions:
        return []
    return versions


def nuget_versions(api_response: Response, queries: dict) -> list:
    """
    Get list of all versions for C# package
    :param queries: compiled jmespath queries
    :param api_response: registry response
    :return: list of versions
    """
    if api_response.status_code == 404:
        return []
    data = api_response.json()
    versions_q: jmespath.parser.ParsedResult = queries["versions"]
    versions = versions_q.search(data)
    if not versions:
        return []
    return versions


def php_versions(api_response: Response, queries: dict) -> list:
    """
    Get list of all versions for php package
    :param queries: compiled jmespath queries
    :param api_response: registry response
    :return: list of versions
    """
    if api_response.status_code == 404:
        return []
    data = api_response.json()
    versions_q: jmespath.parser.ParsedResult = queries["versions"]
    versions = versions_q.search(data)
    if not versions:
        return []
    return versions


def fix_constraint(language: str, reqs: str) -> list[SpecifierSet]:
    """
    Fixes requirement string to be parsed by python requirements
    :param language: language of source code
    :param reqs: requirement info associated with package
    """
    fixed_constraint = reqs.strip()
    if fixed_constraint == "latest":
        all_constraints = [SpecifierSet("==*")]
    match language:
        case "python":
            all_constraints = [SpecifierSet(fixed_constraint)]
        case "javascript":
            # https://docs.npmjs.com/cli/v8/configuring-npm/package-json#dependencies
            all_constraints = []
            # handle logical or
            for sub_constraint in fixed_constraint.split("||"):
                # JavaScript uses `x` as its wildcard character.
                # Replacing '.x' with '.*' should be fine, as `package=x` isn't valid
                # (use `package=*` for that), and for cases like `1.2.3-pre.x`, i think
                # it's fine to have it replaced with `1.2.3-pre.*`.
                sub_constraint = sub_constraint.strip().replace(".x", ".*")
                # range constraints alternative
                if " - " in sub_constraint:
                    sub_constraint = sub_constraint.split(" - ", 1)
                    sub_constraint = f">={sub_constraint[0]}, <={sub_constraint[1]}"
                # handle remaining logical ands
                sub_constraint = re.sub(r"(\s)+(?![A-Za-z0-9])", ",", sub_constraint)
                all_constraints.append(SpecifierSet(sub_constraint))
        case "go":
            # https://go.dev/ref/mod#go-mod-file-require
            all_constraints = [SpecifierSet(fixed_constraint)]
            logging.warning(
                "Lexical comparison used instead of Minimum Version Selection"
            )
        case "cs":
            # https://docs.microsoft.com/en-us/nuget/concepts/package-versioning#version-ranges
            if fixed_constraint[0] == "(":
                ver_spec = fixed_constraint[1:-1].split(",")
                if fixed_constraint[-1] == ")":
                    if ver_spec[0] and not ver_spec[1]:
                        fixed_constraint = ">" + ver_spec[0]
                    elif not ver_spec[0] and ver_spec[1]:
                        fixed_constraint = "<" + ver_spec[1]
                    else:
                        fixed_constraint = ">" + ver_spec[0] + ",<" + ver_spec[1]
                else:
                    if ver_spec[0] and not ver_spec[1]:
                        fixed_constraint = ">" + ver_spec[0]
                    elif not ver_spec[0] and ver_spec[1]:
                        fixed_constraint = "<=" + ver_spec[1]
                    else:
                        fixed_constraint = ">" + ver_spec[0] + ",<=" + ver_spec[1]
            elif fixed_constraint[0] == "[":
                ver_spec = fixed_constraint[1:-1].split(",")
                if fixed_constraint[-1] == ")":
                    if ver_spec[0] and not ver_spec[1]:
                        fixed_constraint = ">=" + ver_spec[0]
                    elif not ver_spec[0] and ver_spec[1]:
                        fixed_constraint = "<" + ver_spec[1]
                    else:
                        fixed_constraint = ">=" + ver_spec[0] + ",<" + ver_spec[1]
                else:
                    if ver_spec[0] and not ver_spec[1]:
                        fixed_constraint = ">=" + ver_spec[0]
                    elif not ver_spec[0] and ver_spec[1]:
                        fixed_constraint = "<=" + ver_spec[1]
                    else:
                        fixed_constraint = ">=" + ver_spec[0] + ",<=" + ver_spec[1]
            else:
                fixed_constraint = ">=" + fixed_constraint
            all_constraints = [SpecifierSet(fixed_constraint)]
        case "php":
            # https://getcomposer.org/doc/articles/versions.md#writing-version-constraints
            all_constraints = []
            # handle logical or
            for sub_constraint in fixed_constraint.replace("||", "|").split("|"):
                # JavaScript uses `x` as its wildcard character.
                # Replacing '.x' with '.*' should be fine, as `package=x` isn't valid
                # (use `package=*` for that), and for cases like `1.2.3-pre.x`, i think
                # it's fine to have it replaced with `1.2.3-pre.*`.
                sub_constraint = sub_constraint.strip()
                # range constraints alternative
                if " - " in sub_constraint:
                    sub_constraint = sub_constraint.split(" - ", 1)
                    sub_constraint = f">={sub_constraint[0]}, <={sub_constraint[1]}"
                # handle remaining logical ands
                sub_constraint = re.sub(r"(\s)+(?![A-Za-z0-9])", ",", sub_constraint)
                all_constraints.append(SpecifierSet(sub_constraint))
        case "rust":
            # https://doc.rust-lang.org/cargo/reference/specifying-dependencies.html
            # Default works like caret
            if fixed_constraint[:1].isalnum():
                fixed_constraint = "^" + fixed_constraint
            all_constraints = [SpecifierSet(fixed_constraint)]
    return all_constraints


def resolve_version(vers: List[str], reqs: List[SpecifierSet] = None) -> Optional[str]:
    """
    Returns latest suitable version from available metadata
    :param vers: list of all available version
    :param reqs: requirement info associated with package
    :return: specific version to query defaults to latest
    """
    compatible_vers = vers
    for req in reqs:
        compatible_vers = [
            ver for ver in compatible_vers if req.specifier.contains(ver)
        ]
    if compatible_vers:
        sorted_vers = sorted(
            compatible_vers,
            key=lambda item1, item2: Version(item1) < Version(item2),
            reverse=True,
        )
        return sorted_vers[0]
    else:
        return None
