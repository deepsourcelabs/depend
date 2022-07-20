"""Test cli and overall pipeline for murdock"""
from pathlib import Path

import pytest
from jsonschema import validate

from depend.cli import main
from depend.error import FileNotSupportedError


class Helpers:
    """Helpers for test"""

    @staticmethod
    def is_valid(json_list):
        """Sets up schema check"""
        j_schema = {
            "type": "array",
            "items": {
                "type": "object",
                "patternProperties": {
                    r"^$|^[\S]+$": {
                        "description": "pkg_name",
                        "type": "object",
                        "properties": {
                            "versions": {
                                "type": "object",
                                "patternProperties": {
                                    r"^$|^[\S]+$": {
                                        "description": "pkg_ver",
                                        "type": "object",
                                        "properties": {
                                            "import_name": {"type": "string"},
                                            "lang_ver": {
                                                "type": "array",
                                                "items": {"type": "string"},
                                            },
                                            "pkg_lic": {
                                                "type": "array",
                                                "items": {"type": "string"},
                                            },
                                            "pkg_err": {"type": "object"},
                                            "pkg_dep": {
                                                "type": "array",
                                                "items": {"type": "string"},
                                            },
                                            "timestamp": {"type": "string"},
                                        },
                                        "additionalProperties": False,
                                    }
                                },
                            },
                        },
                        "required": ["versions"],
                    },
                    "additionalProperties": False,
                },
                "additionalProperties": False,
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
    result = main(
        lang="go",
        packages=None,
        dep_file=Path("tests/data/example_go.mod"),
        depth=None,
    )
    assert json_schema.is_valid(result)


def test_package_json(json_schema):
    """Check package.json file output"""
    result = main(
        lang="javascript",
        packages=None,
        dep_file=Path("tests/data/example_package.json"),
        depth=None,
    )
    assert json_schema.is_valid(result)


def test_npm_shrinkwrap_json(json_schema):
    """Check shrinkwrap file output"""
    result = main(
        lang="javascript",
        packages=None,
        dep_file=Path("tests/data/example_npm_shrinkwrap.json"),
        depth=None,
    )
    assert json_schema.is_valid(result)


def test_package_lock_json(json_schema):
    """Check package lock file output"""
    result = main(
        lang="javascript",
        packages=None,
        dep_file=Path("tests/data/example_package_lock.json"),
        depth=None,
    )
    assert json_schema.is_valid(result)


def test_yarn_v1_lock(json_schema):
    """Check yarn.lock v1 file output"""
    result = main(
        lang="javascript",
        packages=None,
        dep_file=Path("tests/data/example_v1_yarn.lock"),
        depth=None,
    )
    assert json_schema.is_valid(result)


def test_yarn_v2_lock(json_schema):
    """Check yarn.lock v2 file output"""
    result = main(
        lang="javascript",
        packages=None,
        dep_file=Path("tests/data/example_v2_yarn.lock"),
        depth=None,
    )
    assert json_schema.is_valid(result)


def test_requirements_txt(json_schema):
    """Check requirements.txt file output"""
    result = main(
        lang="python",
        packages=None,
        dep_file=Path("tests/data/example_requirements.txt"),
        depth=None,
    )
    assert json_schema.is_valid(result)


def test_setup_py(json_schema):
    """Check setup.py file output"""
    result = main(
        lang="python",
        packages=None,
        dep_file=Path("tests/data/example_setup.py"),
        depth=None,
    )
    assert json_schema.is_valid(result)


def test_setup_cfg(json_schema):
    """Check setup.cfg file output"""
    result = main(
        lang="python",
        packages=None,
        dep_file=Path("tests/data/example_setup.cfg"),
        depth=None,
    )
    assert json_schema.is_valid(result)


def test_pyproject_toml(json_schema):
    """Check toml file output"""
    result = main(
        lang="python",
        packages=None,
        dep_file=Path("tests/data/example_pyproject.toml"),
        depth=None,
    )
    assert json_schema.is_valid(result)


def test_poetry_toml(json_schema):
    """Check poetry toml file output"""
    result = main(
        lang="python",
        packages=None,
        dep_file=Path("tests/data/example_pyproject_poetry.toml"),
        depth=None,
    )
    assert json_schema.is_valid(result)


def test_unsupported(json_schema):
    """Check no extension output"""
    with pytest.raises(FileNotSupportedError, match="example_pipfile"):
        result = main(
            lang="python",
            packages=None,
            dep_file=Path("tests/data/example_pipfile"),
            depth=None,
        )
        assert json_schema.is_valid(result)
