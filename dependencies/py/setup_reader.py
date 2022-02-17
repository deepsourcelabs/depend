"""
Modification of Setup Reader as implemented by Poetry
https://github.com/python-poetry/poetry/blob/master/src/poetry/utils/setup_reader.py
"""

import ast
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
        result = {}

        body = ast.parse(content).body

        setup_call, body = self._find_setup_call(body)
        if not setup_call:
            return self.DEFAULT

        # Inspecting keyword arguments
        result["name"] = self._find_single_string(
            setup_call, body, "name"
        )
        result["version"] = self._find_single_string(
            setup_call, body, "version"
        )
        result["classifiers"] = self._find_single_string(
            setup_call, body, "classifiers"
        )
        result["license"] = self._find_single_string(
            setup_call, body, "license"
        )
        result["python_requires"] = self._find_single_string(
            setup_call, body, "python_requires"
        )
        result["install_requires"] = self._find_install_requires(
            setup_call, body
        )

        return result

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
            if isinstance(elem, ast.With):
                if self.find_variable_in_body(elem.body, name) is not None:
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
        parser = ConfigParser()

        parser.read_string(content)

        name = parser.get("metadata", "name", fallback=None)

        licenses = parser.get("metadata", "license", fallback=None)

        classifiers = parser.get("metadata", "classifiers", fallback=None)

        try:
            version = Version.parse(parser.get("metadata", "version", fallback="")).text
        except exceptions.ParseVersionError:
            version = None

        install_requires = [
            dep.strip() for dep
            in parser.get("options", "install_requires", fallback="").split("\n")
            if dep
        ]

        python_requires = parser.get("options", "python_requires", fallback=None)

        return {
            "name": name,
            "version": version,
            "install_requires": install_requires,
            "python_requires": python_requires,
            "classifiers": classifiers,
            "license": licenses
        }