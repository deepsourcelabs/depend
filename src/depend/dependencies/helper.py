"""Helper Functions for Inspector."""
import datetime
import logging
import re
from typing import List, Optional

import jmespath
import requests
import xmltodict
from bs4 import BeautifulSoup
from packaging.specifiers import InvalidSpecifier, SpecifierSet
from packaging.version import InvalidVersion, Version
from requests import Response

from depend.dep_helper import requests
from depend.error import FileNotSupportedError

from .cs.cs_worker import findkeys, handle_nuspec
from .dep_types import Result
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
                    "pkg_dep": ec.get("pkg_dep") or [],
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
    result["pkg_dep"] = handle_requirements_txt(req_file_data).get("pkg_dep")
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
    pkg_dep, root = parse_nuspec(req_file_data, result)
    result["pkg_dep"] = list(pkg_dep)
    # @type = git
    return root.get("repository", {}).get("@url")


def parse_nuspec(req_file_data, result):
    """Get list of packages from NuSpec"""

    root = xmltodict.parse(req_file_data).get("package", {}).get("metadata")
    result["pkg_name"] = root.get("id")
    result["pkg_ver"] = root.get("version")
    # ignores "file" type
    if root.get("license", {}).get("@type") == "expression":
        result["pkg_lic"] = [root.get("license", {}).get("#text")]
    pkg_dep = set()
    for gen_e in findkeys(root.get("dependencies"), "dependency"):
        if isinstance(gen_e, list):
            for dep_e in gen_e:
                dep_entry = dep_e.get("@id") + ";" + dep_e.get("@version")
                pkg_dep.add(dep_entry)
        else:
            dep_entry = gen_e.get("@id") + ";" + gen_e.get("@version")
            pkg_dep.add(dep_entry)
    return pkg_dep, root


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
        logging.error("Version query failed")
    pkg_lic = ["Other"]
    lic_info = license_q.search(data)
    if isinstance(lic_info, str):
        pkg_lic = lic_info.split(",")
    #     The cases below are just to as to add support for older packages
    elif isinstance(lic_info, dict):
        pkg_lic = [lic_info.get("type", "Other")]
    elif lic_info and isinstance(lic_info, list):
        if isinstance(lic_info[0], dict):
            pkg_lic = list({single_lic.get("type", "Other") for single_lic in lic_info})
        elif isinstance(lic_info[0], str):
            pkg_lic = lic_info
    result["pkg_lic"] = pkg_lic
    dep_data = dependencies_q.search(data)
    if dep_data:
        result["pkg_dep"] = [";".join(tup) for tup in dep_data.items()]
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
    result["pkg_dep"] = [key + ";" + value for (key, value) in dep_data.items()]


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
    result["pkg_dep"] = req_file_data


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
    dependencies_tag = []
    # requirements not version specific
    non_ver_url = url.split("@")[0] + "?tab=imports"
    dep_res = requests.get(non_ver_url, allow_redirects=False)
    if dep_res.status_code == 200:
        dep_soup = BeautifulSoup(dep_res.text, "html.parser")
        dependencies_tag = [
            dependency.getText().strip()
            for dependency in dep_soup.findAll(dep_parse[0], class_=dep_parse[1])
        ]
    result["pkg_name"] = package_name
    result["pkg_ver"] = data[queries["version"]] or ""
    result["pkg_lic"] = [data[queries["license"]] or "Other"]
    result["pkg_dep"] = dependencies_tag


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
    return default_versions(api_response, queries)


def default_versions(api_response, queries):
    """Default API query structure for obtaining versions"""
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
    return default_versions(api_response, queries)


def py_versions(api_response: Response, queries: dict) -> list:
    """
    Get list of all versions for py package
    :param queries: compiled jmespath queries
    :param api_response: registry response
    :return: list of versions
    """
    return default_versions(api_response, queries)


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
    return default_versions(api_response, queries)


def php_versions(api_response: Response, queries: dict) -> list:
    """
    Get list of all versions for php package
    :param queries: compiled jmespath queries
    :param api_response: registry response
    :return: list of versions
    """
    return default_versions(api_response, queries)


def handle_lax_specifier(all_constraints: list[str]) -> list[SpecifierSet]:
    """Attempt to convert list of strings to SpecifierSets"""
    proper_specifiers = []
    for constraint in all_constraints:
        spec = SpecifierSet()
        try:
            spec = SpecifierSet(constraint)
        except InvalidSpecifier:
            try:
                spec = SpecifierSet("==" + constraint.strip())
            except InvalidSpecifier:
                logging.warning(
                    f"Failed to resolve version specification '{constraint}'"
                )
        proper_specifiers.append(spec)
    return proper_specifiers


def fix_constraint(language: str, reqs: str) -> list[SpecifierSet]:
    """
    Fixes requirement string to be parsed by python requirements
    :param language: language of source code
    :param reqs: requirement info associated with package
    """
    all_constraints = []
    fixed_constraint = reqs.strip()
    if fixed_constraint in ("latest", "*", "") or not fixed_constraint:
        return [SpecifierSet()]
    match language:
        case "python":
            all_constraints = [
                ",".join(
                    [
                        fix_constraint_py(constraint)
                        for constraint in fixed_constraint.split(",")
                    ]
                )
            ]
        case "javascript":
            # JS supports * or x as a direct major ver wildcard
            # https://docs.npmjs.com/cli/v8/configuring-npm/package-json#dependencies
            # handle logical or
            for sub_constraint in fixed_constraint.split("||"):
                sub_constraint = ",".join(
                    [
                        fix_constraint_js(constraint)
                        for constraint in sub_constraint.split(",")
                    ]
                )
                all_constraints.append(sub_constraint)
        case "go":
            # https://go.dev/ref/mod#go-mod-file-require
            all_constraints = [">=" + fixed_constraint]
        case "cs":
            # https://docs.microsoft.com/en-us/nuget/concepts/package-versioning#version-ranges
            all_constraints = [fix_constraint_cs(fixed_constraint)]
        case "php":
            # https://getcomposer.org/doc/articles/versions.md#writing-version-constraints
            # handle logical or
            for sub_constraint in fixed_constraint.replace("||", "|").split("|"):
                sub_constraint = ",".join(
                    [
                        fix_constraint_php(constraint)
                        for constraint in sub_constraint.split(",")
                    ]
                )
                all_constraints.append(sub_constraint)
        case "rust":
            # https://doc.rust-lang.org/cargo/reference/specifying-dependencies.html
            all_constraints = [
                ",".join(
                    [
                        fix_constraint_rust(constraint)
                        for constraint in fixed_constraint.split(",")
                    ]
                )
            ]
    return handle_lax_specifier(all_constraints)


def fix_constraint_rust(fixed_constraint: str) -> str:
    """Rust version constrains to Python"""
    # Default works like caret
    if "*" not in fixed_constraint:
        if "~" in fixed_constraint:
            fixed_constraint = handle_tilde(fixed_constraint)
        elif fixed_constraint[:1].isalnum():
            fixed_constraint = "^" + fixed_constraint
        if "^" in fixed_constraint:
            fixed_constraint = handle_caret(fixed_constraint)
    return fixed_constraint


def fix_constraint_php(sub_constraint: str) -> str:
    """PHP version constrains to Python"""
    sub_constraint = sub_constraint.strip()
    # range constraints alternative
    if " - " in sub_constraint:
        sub_constraint = sub_constraint.split(" - ", 1)
        sub_constraint = f">={sub_constraint[0]}, <={sub_constraint[1]}"
    if "^" in sub_constraint:
        sub_constraint = handle_caret(sub_constraint)
    if "~" in sub_constraint:
        sub_constraint = handle_tilde(sub_constraint, True)
    # handle remaining logical ands
    sub_constraint = re.sub(r"(\s)+(?!\w)", ",", sub_constraint)
    return sub_constraint


def fix_constraint_cs(fixed_constraint: str) -> str:
    """C# version constrains to Python"""
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
        if len(ver_spec) == 1:
            fixed_constraint = "==" + ver_spec[0]
        elif fixed_constraint[-1] == ")":
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
    return fixed_constraint


def fix_constraint_js(sub_constraint: str) -> str:
    """JavaScript version constrains to Python"""
    # JavaScript uses `x` as its wildcard character.
    # Replacing '.x' with '.*' should be fine, as `package=x` isn't valid
    # (use `package=*` for that), and for cases like `1.2.3-pre.x`, i think
    # it's fine to have it replaced with `1.2.3-pre.*`.
    sub_constraint = sub_constraint.strip().replace(".x", ".*")
    if "^" in sub_constraint:
        sub_constraint = handle_caret(sub_constraint)
    if "~" in sub_constraint:
        sub_constraint = handle_tilde(sub_constraint)
    # range constraints alternative
    if " - " in sub_constraint:
        sub_constraint = sub_constraint.split(" - ", 1)
        sub_constraint = f">={sub_constraint[0]}, <={sub_constraint[1]}"
    # handle remaining logical ands
    sub_constraint = re.sub(r"(\s)+(?!\w)", ",", sub_constraint)
    return sub_constraint


def fix_constraint_py(fixed_constraint: str) -> str:
    """Python non standard version constrains handling"""
    # handle poetry spec of tilde requirements
    # fixed_constraint = re.sub(r"=*~(?!=)", "~=", fixed_constraint)
    # caret requirements
    if "^" in fixed_constraint:
        fixed_constraint = handle_caret(fixed_constraint)
    if "~" in fixed_constraint and "~=" not in fixed_constraint:
        fixed_constraint = handle_tilde(fixed_constraint)
    return fixed_constraint


def resolve_version(vers: List[str], reqs: List[SpecifierSet] = None) -> Optional[str]:
    """
    Returns latest suitable version from available metadata
    :param vers: list of all available version
    :param reqs: requirement info associated with package
    :return: specific version to query defaults to latest
    """
    compatible_vers = vers
    or_compatible = []
    for req in reqs:
        or_compatible.extend([ver for ver in compatible_vers if req.contains(ver)])
    if or_compatible:
        sorted_vers = sorted(
            or_compatible,
            key=try_version,
            reverse=True,
        )
        return sorted_vers[0]
    else:
        return None


def handle_caret(req: str) -> str:
    """Handle caret based requirement constraints"""
    _, version = req.split("^", 1)
    major, minor, patch, *_ = (version + "...").split(".")
    if patch:
        if minor == "0" and major == "0":
            limit = f"0.0.{int(patch) + 1}"
        elif major == "0":
            limit = f"0.{int(minor) + 1}.0"
        else:
            limit = f"{int(major) + 1}.0.0"
    elif minor:
        if major == "0":
            limit = f"0.{int(minor) + 1}.0"
        else:
            limit = f"{int(major) + 1}.0.0"
    else:
        limit = f"{int(major) + 1}.0.0"
    return f">={version},<{limit}"


def handle_tilde(req: str, is_php: bool = False) -> str:
    """Handle tilde based requirement constraints"""
    _, version = req.split("~", 1)
    major, minor, patch, *_ = (version + "...").split(".")
    if patch:
        limit = f"{major}.{int(minor) + 1}.0"
    elif minor and not is_php:
        # if major.minor is given php wont lock the minor version
        limit = f"{major}.{int(minor) + 1}.0"
    else:
        limit = f"{int(major) + 1}.0.0"
    return f">={version},<{limit}"


def try_version(value):
    """If version parsing fails defer the version"""
    try:
        return Version(value)
    except InvalidVersion:
        return Version("9999.9999.9999")
