"""
Modification of Setup Reader as implemented by Poetry
https://github.com/python-poetry/poetry/blob/master/src/poetry/utils/setup_reader.py
"""

import ast
import re
from configparser import ConfigParser
from typing import Any
from typing import Dict
from typing import Iterable
from typing import List
from typing import Optional
from typing import Union
from poetry.core.semver import Version
from poetry.core.semver import exceptions
from poetry.utils.setup_reader import SetupReader


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
        res["lang_ver"] = ";".join(lang)
    if not res["pkg_lic"] or res["pkg_lic"] == "Other":
        lic = re.findall(r'License :: ([^"\n]+)', classifiers)
        res["pkg_lic"] = ";".join(lic)


class LaxSetupReader(SetupReader):
    """
    Class that reads a setup.py file without executing it.
    """

    def read_setup_py(
            self, content: str
    ) -> Dict[str, Union[List, Dict]]:
        """
        Directly reads setup.py content and returns key info
        :param content: content of setup.py
        :return: info required by dependency inspector
        """
        res = {
            "lang_ver": "",
            "pkg_name": "",
            "pkg_ver": "",
            "pkg_lic": "",
            "pkg_err": "",
            "pkg_dep": [],
        }
        body = ast.parse(content).body

        setup_call, body = self._find_setup_call(body)
        if not setup_call:
            return self.DEFAULT

        # Inspecting keyword arguments
        res["pkg_name"] = self._find_single_string(
            setup_call, body, "name"
        )
        res["pkg_ver"] = self._find_single_string(
            setup_call, body, "version"
        )
        res["pkg_lic"] = self._find_single_string(
            setup_call, body, "license"
        )
        res["lang_ver"] = self._find_single_string(
            setup_call, body, "python_requires"
        ).replace(",", ";")
        res["pkg_dep"] = self._find_install_requires(
            setup_call, body
        )
        classifiers = self._find_single_string(
            setup_call, body, "classifiers"
        )
        if classifiers:
            handle_classifiers(classifiers, res)
        return res

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
            return value.s
        elif isinstance(value, ast.Name):
            variable = self._find_variable_in_body(body, value.id)

            if variable is not None and isinstance(variable, ast.Str):
                return variable.s

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
            for el in value.elts:
                install_requires.append(el.s)
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
            "lang_ver": "",
            "pkg_name": "",
            "pkg_ver": "",
            "pkg_lic": "",
            "pkg_err": "",
            "pkg_dep": [],
        }
        parser = ConfigParser()
        parser.read_string(content)
        res["pkg_name"] = parser.get("metadata", "name", fallback=None)
        res["pkg_lic"] = parser.get("metadata", "license", fallback=None)
        classifiers = parser.get("metadata", "classifiers", fallback=None)
        try:
            res["pkg_ver"] = Version.parse(parser.get("metadata", "version", fallback="")).text
        except exceptions.ParseVersionError:
            res["pkg_ver"] = ""
        res["pkg_dep"] = [
            dep.strip() for dep
            in parser.get("options", "install_requires", fallback="").split("\n")
            if dep
        ]
        res["lang_ver"] = parser.get(
            "options", "python_requires", fallback=""
        ).replace(",", ";")
        if classifiers:
            handle_classifiers(classifiers, res)
        return res
