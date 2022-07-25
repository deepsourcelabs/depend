"""
Modification of Setup Reader as implemented by Poetry
https://github.com/python-poetry/poetry/blob/master/src/poetry/utils/setup_reader.py
"""

import ast
import logging
import re
from configparser import ConfigParser
from datetime import datetime
from typing import Any, Iterable, List, Match, Optional, Union

import github
from github.ContentFile import ContentFile
from poetry.core.semver import Version, exceptions
from poetry.utils.setup_reader import SetupReader

from depend.dependencies.dep_types import Result
from depend.dependencies.py.py_helper import handle_requirements_txt
from depend.handle_env import get_github


def find_github(text: str) -> Match[str] | None:
    """
    Returns a repo url from a string
    :param text: string to check
    """
    repo_identifier = re.search(
        r"github.com/([^/]+)/([^/.\r\n\'\"]+)(?:/tree/|)?([^/.\r\n\'\"]+)?", text
    )
    return repo_identifier


def handle_classifiers(classifiers, res):
    """
    Obtains missing info from classifiers
    :param classifiers: content used for indexing in pypi
    :param res: dict to modify
    """
    if not res["lang_ver"]:
        lang = re.findall(r'Programming Language :: Python :: ([^"\n]+)', classifiers)
        res["lang_ver"] = lang
    if not res["pkg_lic"] or res["pkg_lic"][0] == "Other":
        lic = re.findall(r'License :: ([^"\n]+)', classifiers)
        res["pkg_lic"] = lic


class LaxSetupReader(SetupReader):
    """
    Read the setup.py file without executing it.
    """

    def auth_read_setup_py(self, content: str) -> Result:
        """
        Directly read setup.py content
        :param content: content of setup.py
        :return: {
            "name": package name,
            "version": package version,
            "install_requires": list of packages required
                or a string with file to be read from repo
            "python_requires": python versions,
            "classifiers": data provided for indexing,
            "license": list of licenses found
        }
        """
        res: Result = {
            "import_name": "",
            "lang_ver": [],
            "pkg_name": "",
            "pkg_ver": "",
            "pkg_lic": ["Other"],
            "pkg_err": {},
            "pkg_dep": [],
            "timestamp": datetime.utcnow().isoformat(),
        }
        body = ast.parse(content).body
        repo_identifier = find_github(content)
        setup_call, body = self._find_setup_call(body)
        if not setup_call:
            return res

        # Inspecting keyword arguments
        res["pkg_name"] = self._find_single_string(setup_call, body, "name")
        import_options = self._find_single_string(setup_call, body, "packages")
        res["pkg_ver"] = self._find_single_string(setup_call, body, "version")
        if pkg_lic := self._find_single_string(setup_call, body, "license"):
            res["pkg_lic"] = [pkg_lic]
        if lang_ver := self._find_single_string(setup_call, body, "python_requires"):
            res["lang_ver"] = lang_ver.split(",")
        pkg_dep = self._find_install_requires(setup_call, body)
        if isinstance(pkg_dep, str) and repo_identifier:
            g = get_github()
            logging.info("Repo: %s", repo_identifier.groups())
            repo = g.get_repo(repo_identifier.group(1) + "/" + repo_identifier.group(2))
            commit_branch_tag = repo_identifier.group(3) or repo.default_branch
            try:
                repo_file_content = repo.get_contents(pkg_dep, ref=commit_branch_tag)
                if isinstance(repo_file_content, ContentFile):
                    dep_file = repo_file_content.decoded_content.decode()
                    res["pkg_dep"] = handle_requirements_txt(dep_file).get(
                        "pkg_dep", []
                    )
            except github.GithubException as e:
                logging.error(e)
        else:
            res["pkg_dep"] = handle_requirements_txt("\n".join(pkg_dep)).get(
                "pkg_dep", {}
            )
        classifiers = self._find_single_string(setup_call, body, "classifiers")
        if classifiers:
            handle_classifiers(classifiers, res)
        if import_options:
            res["import_name"] = import_options.split("\n")[0]
        return res

    def _find_in_dict(self, dict_: ast.Dict, name: str) -> Optional[Any]:
        for key, val in zip(dict_.keys, dict_.values):
            if isinstance(key, ast.Str) and key.s == name:
                return val
        return None

    def _find_single_string(self, call: ast.Call, body: List[Any], name: str) -> str:
        value = self._find_in_call(call, name)
        if value is None:
            # Trying to find in kwargs
            kwargs = self._find_call_kwargs(call)

            if kwargs is None or not isinstance(kwargs, ast.Name):
                return ""

            variable = self._find_variable_in_body(body, kwargs.id)
            if not isinstance(variable, (ast.Dict, ast.Call)):
                return ""

            if isinstance(variable, ast.Call):
                if not isinstance(variable.func, ast.Name):
                    return ""

                if variable.func.id != "dict":
                    return ""

                value = self._find_in_call(variable, name)
            else:
                value = self._find_in_dict(variable, name)

        if value is None:
            return ""

        if isinstance(value, ast.Str):
            return value.s or ""
        if isinstance(value, ast.List):
            out = ""
            for subnode in value.elts:
                if isinstance(subnode, ast.Str):
                    out = out + subnode.s + "\n"
            return out or ""
        elif isinstance(value, ast.Name):
            variable = self._find_variable_in_body(body, value.id)

            if variable is not None and isinstance(variable, ast.Str):
                return variable.s or ""
        return ""

    def _find_install_requires(
        self, call: ast.Call, body: Iterable[Any]
    ) -> Union[List[str], str]:
        """
        Analyze setup.py and find dependencies
        :param call: setup function in setup.py
        :param body: body for variable definitions
        :return: package dependencies list or file to query
        """
        install_requires: List[str] = []
        value = self._find_in_call(call, "install_requires")
        if value is None:
            # Trying to find in kwargs
            kwargs = self._find_call_kwargs(call)

            if kwargs is None or not isinstance(kwargs, ast.Name):
                return install_requires

            variable = self._find_variable_in_body(body, kwargs.id)
            if not isinstance(variable, (ast.Dict, ast.Call)):
                return install_requires

            if isinstance(variable, ast.Call):
                if not isinstance(variable.func, ast.Name):
                    return install_requires

                if variable.func.id != "dict":
                    return install_requires

                value = self._find_in_call(variable, "install_requires")
            else:
                value = self._find_in_dict(variable, "install_requires")

        if value is None:
            return install_requires

        elif isinstance(value, ast.List):
            for el_n in value.elts:
                if isinstance(el_n, ast.Name):
                    variable = self.find_variable_in_body(body, el_n.id)

                    if variable is not None and isinstance(variable, ast.List):
                        for el in variable.elts:
                            if isinstance(el, ast.Constant):
                                install_requires.append(el.s)

                    elif variable is not None and isinstance(variable, ast.Constant):
                        install_requires.append(variable.s)

                    # ignores other instances possible
        elif isinstance(value, ast.Name):
            variable = self.find_variable_in_body(body, value.id)

            if variable is not None and isinstance(variable, ast.List):
                for el in variable.elts:
                    if isinstance(el, ast.Constant):
                        install_requires.append(el.s)

            elif variable is not None and isinstance(variable, str):
                return variable

        return install_requires

    def find_variable_in_body(self, body: Iterable[Any], name: str) -> Optional[Any]:
        """
        Considers with body as well
        :param body: ast body to search in
        :param name: variable being searched for
        :return: variable value
        """
        for elem in body:
            # checks if filename is found in with
            if (
                isinstance(elem, ast.With)
                and self.find_variable_in_body(elem.body, name) is not None
            ):
                for item in elem.items:
                    if not isinstance(item, ast.withitem):
                        continue
                    cont = item.context_expr
                    if not isinstance(cont, ast.Call):
                        continue
                    func = cont.func
                    if not (isinstance(func, ast.Name) and func.id == "open"):
                        continue
                    for arg in cont.args:
                        if not (isinstance(arg, ast.Constant)):
                            return "check_all_paths"
                        return arg.value

            if not isinstance(elem, ast.Assign):
                continue

            for target in elem.targets:
                if not isinstance(target, ast.Name):
                    continue

                if target.id == name:
                    return elem.value
        return None

    def read_setup_cfg(self, content: str) -> Result:
        """
        Analyzes content of setup.cfg
        :param content: file content
        :return: filtered metadata
        """
        res: Result = {
            "import_name": "",
            "lang_ver": [],
            "pkg_name": "",
            "pkg_ver": "",
            "pkg_lic": ["Other"],
            "pkg_err": {},
            "pkg_dep": [],
            "timestamp": datetime.utcnow().isoformat(),
        }
        parser = ConfigParser()
        parser.read_string(content)
        res["pkg_name"] = parser.get("metadata", "name", fallback="")
        res["pkg_lic"] = [parser.get("metadata", "license", fallback="Other")]
        classifiers = parser.get("metadata", "classifiers", fallback=None)
        try:
            res["pkg_ver"] = Version.parse(
                parser.get("metadata", "version", fallback="")
            ).text
        except exceptions.ParseVersionError:
            res["pkg_ver"] = ""
        res["pkg_dep"] = handle_requirements_txt(
            parser.get("options", "install_requires", fallback="")
        ).get("pkg_dep")
        res["lang_ver"] = parser.get("options", "python_requires", fallback="").split(
            ","
        )
        if classifiers:
            handle_classifiers(classifiers, res)
        return res
