"""Tests output obtained by parsing dependency files"""

import dependencies.go.go_worker
import dependencies.js.js_worker
import dependencies.py.py_worker

import pytest
from jsonschema import validate


class Helpers:
    """Helpers for test"""

    @staticmethod
    def is_valid(json_list):
        """Sets up schema check"""
        j_schema = {
            "type": "object",
            "properties": {
                "lang_ver": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    }
                },
                "pkg_name": {
                    "type": "string"
                },
                "pkg_ver": {
                    "type": "string"
                },
                "pkg_dep": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    }
                },
                "pkg_err": {
                    "type": "object"
                },
                "pkg_lic": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    }
                },
                "timestamp": {
                    "type": "string"
                }
            }}
        validate(instance=json_list, schema=j_schema)
        return True


@pytest.fixture
def json_schema():
    """Schema helper functions"""
    return Helpers


def test_go_mod(json_schema):
    """Check go.mod file output"""
    with open("tests/data/example_go.mod") as f:
        mod_content = f.read()
    result = dependencies.go.go_worker.handle_go_mod(mod_content)
    assert json_schema.is_valid(result)


def test_package_json(json_schema):
    """Check package.json file output"""
    with open("tests/data/example_package.json") as f:
        json_content = f.read()
    result = dependencies.js.js_worker.handle_json(json_content)
    assert json_schema.is_valid(result)


def test_npm_shrinkwrap_json(json_schema):
    """Check package.json file output"""
    with open("tests/data/example_npm_shrinkwrap.json") as f:
        json_content = f.read()
    result = dependencies.js.js_worker.handle_json(json_content)
    assert json_schema.is_valid(result)


def test_package_lock_json(json_schema):
    """Check package.json file output"""
    with open("tests/data/example_package_lock.json") as f:
        json_content = f.read()
    result = dependencies.js.js_worker.handle_json(json_content)
    assert json_schema.is_valid(result)


def test_yarn_v1_lock(json_schema):
    """Check yarn.lock v1 file output"""
    with open("tests/data/example_v1_yarn.lock") as f:
        yarn_content = f.read()
    result = dependencies.js.js_worker.handle_yarn_lock(yarn_content)
    assert json_schema.is_valid(result)


def test_yarn_v2_lock(json_schema):
    """Check yarn.lock v2 file output"""
    with open("tests/data/example_v2_yarn.lock") as f:
        yarn_content = f.read()
    result = dependencies.js.js_worker.handle_yarn_lock(yarn_content)
    assert json_schema.is_valid(result)


def test_requirements_txt(json_schema):
    """Check requirements.txt file output"""
    with open("tests/data/example_requirements.txt") as f:
        txt_content = f.read()
    result = dependencies.py.py_worker.handle_requirements_txt(txt_content)
    assert json_schema.is_valid(result)


def test_setup_py(json_schema):
    """Check setup.py file output"""
    with open("tests/data/example_setup.py") as f:
        py_content = f.read()
    result = dependencies.py.py_worker.handle_setup_py(py_content)
    assert json_schema.is_valid(result)


def test_setup_cfg(json_schema):
    """Check setup.cfg file output"""
    with open("tests/data/example_setup.cfg") as f:
        cfg_content = f.read()
    result = dependencies.py.py_worker.handle_setup_cfg(cfg_content)
    assert json_schema.is_valid(result)


def test_pyproject_toml(json_schema):
    """Check toml file output"""
    with open("tests/data/example_pyproject.toml") as f:
        pyproject = f.read()
    result = dependencies.py.py_worker.handle_toml(pyproject)
    assert json_schema.is_valid(result)


def test_poetry_toml(json_schema):
    """Check poetry toml file output"""
    with open("tests/data/example_pyproject_poetry.toml") as f:
        pyproject = f.read()
    result = dependencies.py.py_worker.handle_toml(pyproject)
    assert json_schema.is_valid(result)


def test_other_py(json_schema):
    """
    Parses conda.yml tox.ini and Pipfiles
    """
    with open("tests/data/example_pipfile") as f:
        pyproject = f.read()
    result = dependencies.py.py_worker.handle_otherpy(pyproject, "Pipfile")
    assert json_schema.is_valid(result)
