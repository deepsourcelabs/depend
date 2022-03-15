"""
Modification of Setup Reader as implemented by Poetry
https://github.com/python-poetry/poetry/blob/master/src/poetry/utils/setup_reader.py
"""

import ast
import logging
import re
from configparser import ConfigParser
from datetime import datetime
from typing import Any, Match
from typing import Dict
from typing import Iterable
from typing import List
from typing import Optional
from typing import Union

import github
from poetry.core.semver import Version
from poetry.core.semver import exceptions
from poetry.utils.setup_reader import SetupReader

from dependencies.py import py_worker


def find_github(text: str) -> Match[str] | None:
    """
    Returns a repo url from a string
    :param text: string to check
    """
    repo_identifier = re.search(
        r"github.com/([^/]+)/([^/.\r\n]+)(?:/tree/|)?([^/.\r\n]+)?",
        text
    )
    return repo_identifier


def handle_classifiers(classifiers, res):
    """
    Obtains missing info from classifiers
    :param classifiers: content used for indexing in pypi
    :param res: dict to modify
    """
    if not res["lang_ver"]:
        lang = re.findall(
            r'Programming Language :: Python :: ([^"\n]+)',
            classifiers
        )
        res["lang_ver"] = lang
    if not res["pkg_lic"] or res["pkg_lic"][0] == "Other":
        lic = re.findall(r'License :: ([^"\n]+)', classifiers)
        res["pkg_lic"] = lic


class LaxSetupReader(SetupReader):
    """
    Class that reads a setup.py file without executing it.
    """

    def read_setup_py(
            self, content: str, gh_token: str = None
    ) -> Dict[str, Union[List, Dict]]:
        """
        Directly reads setup.py content and returns key info
        :param gh_token: GitHub token
        :param content: content of setup.py
        :return: info required by dependency inspector
        """
        res = {
            "import_name": "",
            "lang_ver": [],
            "pkg_name": "",
            "pkg_ver": "",
            "pkg_lic": ["Other"],
            "pkg_err": {},
            "pkg_dep": [],
            'timestamp': datetime.utcnow().isoformat()
        }
        body = ast.parse(content).body
        repo_identifier = find_github(content)
        setup_call, body = self._find_setup_call(body)
        if not setup_call:
            return self.DEFAULT

        # Inspecting keyword arguments
        res["pkg_name"] = self._find_single_string(
            setup_call, body, "name"
        )
        import_options = self._find_single_string(
            setup_call, body, "packages"
        )
        res["pkg_ver"] = self._find_single_string(
            setup_call, body, "version"
        )
        if pkg_lic := self._find_single_string(
            setup_call, body, "license"
        ):
            res["pkg_lic"] = [pkg_lic]
        if lang_ver := self._find_single_string(
                setup_call, body, "python_requires"
            ):
            res["lang_ver"] = lang_ver.split(",")
        pkg_dep = self._find_install_requires(
            setup_call, body
        )
        if isinstance(pkg_dep, str) and repo_identifier:
            g = github.Github(gh_token)
            repo = g.get_repo(repo_identifier.group(1) + "/" + repo_identifier.group(2))
            commit_branch_tag = repo_identifier.group(3) or repo.default_branch
            try:
                dep_file = repo.get_contents(
                    pkg_dep,
                    ref=commit_branch_tag
                ).decoded_content.decode()
                res["pkg_dep"] = py_worker.handle_requirements_txt(
                    dep_file
                ).get("pkg_dep")
            except github.GithubException as e:
                logging.error(e)
        else:
            res["pkg_dep"] = py_worker.handle_requirements_txt(
                "\n".join(pkg_dep)
            ).get("pkg_dep")
        classifiers = self._find_single_string(
            setup_call, body, "classifiers"
        )
        if classifiers:
            handle_classifiers(classifiers, res)
        if import_options:
            res["import_name"] = import_options.split("\n")[0]
        return res

    def _find_in_dict(self, dict_: ast.Dict, name: str) -> Optional[Any]:
        for key, val in zip(dict_.keys, dict_.values):
            if isinstance(key, ast.Str) and key.s == name:
                return val

    def _find_single_string(
            self, call: ast.Call,
            body: List[Any], name: str
    ) -> str:
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

    # noinspection PyUnresolvedReferences
    def _find_install_requires(
            self, call: ast.Call, body: Iterable[Any]
    ) -> Union[List[str], str]:
        install_requires = []
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

        if isinstance(value, ast.List):
            for el_n in value.elts:
                if isinstance(el_n, ast.Name):
                    variable = self.find_variable_in_body(body, el_n.id)

                    if variable is not None and isinstance(variable, ast.List):
                        for el in variable.elts:
                            install_requires.append(el.s)

                    elif variable is not None and isinstance(variable, str):
                        install_requires.append(el_n.s)
                else:
                    install_requires.append(el_n.s)
        elif isinstance(value, ast.Name):
            variable = self.find_variable_in_body(body, value.id)

            if variable is not None and isinstance(variable, ast.List):
                for el in variable.elts:
                    install_requires.append(el.s)

            elif variable is not None and isinstance(variable, str):
                return variable

        return install_requires

    def find_variable_in_body(
            self, body: Iterable[Any], name: str
    ) -> Optional[Any]:
        """
        Considers with body as well
        :param body: ast body to search in
        :param name: variable being searched for
        :return: variable value
        """
        found = None
        for elem in body:
            if found:
                break

            # checks if filename is found in with
            if isinstance(elem, ast.With) and self.find_variable_in_body(elem.body, name) is not None:
                for item in elem.items:
                    if not isinstance(item, ast.withitem):
                        continue
                    cont = item.context_expr
                    if not isinstance(cont, ast.Call):
                        continue
                    func = cont.func
                    if not (isinstance(func, ast.Name)
                            and func.id == "open"):
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

    def read_setup_cfg(
            self, content: str
    ) -> Dict[str, Union[List, Dict]]:
        """
        Analyzes content of setup.cfg
        :param content: file content
        :return: filtered metadata
        """
        res = {
            "lang_ver": [],
            "pkg_name": "",
            "pkg_ver": "",
            "pkg_lic": ["Other"],
            "pkg_err": {},
            "pkg_dep": [],
            'timestamp': datetime.utcnow().isoformat()
        }
        parser = ConfigParser()
        parser.read_string(content)
        res["pkg_name"] = parser.get("metadata", "name", fallback="")
        res["pkg_lic"] = [parser.get("metadata", "license", fallback="Other")]
        classifiers = parser.get("metadata", "classifiers", fallback=None)
        try:
            res["pkg_ver"] = Version.parse(parser.get("metadata", "version", fallback="")).text
        except exceptions.ParseVersionError:
            res["pkg_ver"] = ""
        res["pkg_dep"] = py_worker.handle_requirements_txt(
            parser.get("options", "install_requires", fallback="")
        ).get("pkg_dep")
        res["lang_ver"] = parser.get(
            "options", "python_requires", fallback=""
        ).split(",")
        if classifiers:
            handle_classifiers(classifiers, res)
        return res
