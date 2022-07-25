"""Tests output obtained by parsing dependency files"""
import pytest
from jsonschema import validate

import depend.dependencies.cs.cs_worker as cs_worker
import depend.dependencies.go.go_worker as go_worker
import depend.dependencies.js.js_worker as js_worker
import depend.dependencies.php.php_worker as php_worker
import depend.dependencies.py.py_helper as py_helper
import depend.dependencies.py.py_worker as py_worker
import depend.dependencies.rust.rust_worker as rust_worker


class Helpers:
    """Helpers for test"""

    @staticmethod
    def is_valid(json_list):
        """Sets up schema check"""
        j_schema = {
            "type": "object",
            "properties": {
                "lang_ver": {"type": "array", "items": {"type": "string"}},
                "pkg_name": {"type": "string"},
                "pkg_ver": {"type": "string"},
                "pkg_dep": {
                    "anyOf": [
                        {"type": "array", "items": {"type": "string"}},
                        {"type": "null"},
                    ]
                },
                "pkg_err": {"type": "object"},
                "pkg_lic": {"type": "array", "items": {"type": "string"}},
                "timestamp": {"type": "string"},
            },
        }
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
    result = go_worker.handle_go_mod(mod_content)
    assert json_schema.is_valid(result)


def test_package_json(json_schema):
    """Check package.json file output"""
    with open("tests/data/example_package.json") as f:
        json_content = f.read()
    result = js_worker.handle_json(json_content)
    assert json_schema.is_valid(result)


def test_npm_shrinkwrap_json(json_schema):
    """Check package.json file output"""
    with open("tests/data/example_npm_shrinkwrap.json") as f:
        json_content = f.read()
    result = js_worker.handle_json(json_content)
    assert json_schema.is_valid(result)


def test_package_lock_json(json_schema):
    """Check package.json file output"""
    with open("tests/data/example_package_lock.json") as f:
        json_content = f.read()
    result = js_worker.handle_json(json_content)
    assert json_schema.is_valid(result)


def test_yarn_v1_lock(json_schema):
    """Check yarn.lock v1 file output"""
    with open("tests/data/example_v1_yarn.lock") as f:
        yarn_content = f.read()
    result = js_worker.handle_yarn_lock(yarn_content)
    assert json_schema.is_valid(result)


def test_yarn_v2_lock(json_schema):
    """Check yarn.lock v2 file output"""
    with open("tests/data/example_v2_yarn.lock") as f:
        yarn_content = f.read()
    result = js_worker.handle_yarn_lock(yarn_content)
    assert json_schema.is_valid(result)


def test_requirements_txt(json_schema):
    """Check requirements.txt file output"""
    with open("tests/data/example_requirements.txt") as f:
        txt_content = f.read()
    result = py_helper.handle_requirements_txt(txt_content)
    assert json_schema.is_valid(result)


def test_setup_py(json_schema):
    """Check setup.py file output"""
    with open("tests/data/example_setup.py") as f:
        py_content = f.read()
    result = py_worker.handle_setup_py(py_content)
    assert json_schema.is_valid(result)


def test_setup_cfg(json_schema):
    """Check setup.cfg file output"""
    with open("tests/data/example_setup.cfg") as f:
        cfg_content = f.read()
    result = py_worker.handle_setup_cfg(cfg_content)
    assert json_schema.is_valid(result)


def test_pyproject_toml(json_schema):
    """Check toml file output"""
    with open("tests/data/example_pyproject.toml") as f:
        pyproject = f.read()
    result = py_worker.handle_toml(pyproject)
    assert json_schema.is_valid(result)


def test_poetry_toml(json_schema):
    """Check poetry toml file output"""
    with open("tests/data/example_pyproject_poetry.toml") as f:
        pyproject = f.read()
    result = py_worker.handle_toml(pyproject)
    assert json_schema.is_valid(result)


def test_other_py(json_schema):
    """
    Parses conda.yml tox.ini and Pipfiles
    """
    with open("tests/data/example_pipfile") as f:
        pyproject = f.read()
    result = py_worker.handle_otherpy(pyproject, "Pipfile")
    assert json_schema.is_valid(result)


def test_cs_xml(json_schema):
    """Parses nuspec files"""
    with open("tests/data/example_package.nuspec") as f:
        nuspec = f.read()
    result = cs_worker.handle_nuspec(nuspec)
    assert json_schema.is_valid(result)


def test_composer_json(json_schema):
    """Check composer json file output"""
    with open("tests/data/example_composer.json") as f:
        php_project = f.read()
    result = php_worker.handle_composer_json(php_project)
    assert json_schema.is_valid(result)


def test_cargo_toml(json_schema):
    """Check cargo toml file output"""
    with open("tests/data/example_cargo.toml") as f:
        rust_project = f.read()
    result = rust_worker.handle_cargo_toml(rust_project)
    assert json_schema.is_valid(result)


def test_cargo_lock(json_schema):
    """Check poetry toml file output"""
    with open("tests/data/example_cargo.lock") as f:
        rust_project = f.read()
    result = rust_worker.handle_lock(rust_project)
    assert json_schema.is_valid(result)
