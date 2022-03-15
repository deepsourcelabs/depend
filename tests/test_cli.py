"""Test cli and overall pipeline for dependency-inspector"""
import logging
from pathlib import Path

import pytest
from jsonschema import validate

from cli import main
from error import FileNotSupportedError

LOGGER = logging.getLogger(__name__)


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
                                            "import_name": {
                                                "type": "string"
                                            },
                                            "lang_ver": {
                                                "type": "array",
                                                "items": {
                                                    "type": "string"
                                                }
                                            },
                                            "pkg_lic": {
                                                "type": "array",
                                                "items": {
                                                    "type": "string"
                                                }
                                            },
                                            "pkg_err": {
                                                "type": "object"
                                            },
                                            "pkg_dep": {
                                                "type": "array",
                                                "items": {
                                                    "type": "string"
                                                }
                                            },
                                            "timestamp": {
                                                "type": "string"
                                            }
                                        },
                                        "additionalProperties": False
                                    }
                                }
                            },
                        },
                        "required": ["versions"]
                    },
                    "additionalProperties": False,
                },
                "additionalProperties": False,
            }
        }
        validate(instance=json_list, schema=j_schema)
        return True


@pytest.fixture
def config_file():
    """Reads config file"""
    parent_folder = Path(__file__).parent.parent
    return Path.joinpath(parent_folder, "configuration.ini")


@pytest.fixture
def json_schema():
    """Schema helper functions"""
    return Helpers


def test_go_mod(json_schema, config_file):
    """Check go.mod file output"""
    result = main(
        lang="go",
        dep_file=Path("tests/data/example_go.mod"),
        deep_search=True,
        host=None,
        config=config_file
    )
    assert json_schema.is_valid(result)


def test_package_json(json_schema, config_file):
    """Check package.json file output"""
    result = main(
        lang="javascript",
        dep_file=Path("tests/data/example_package.json"),
        deep_search=True,
        host=None,
        config=config_file
    )
    assert json_schema.is_valid(result)


def test_npm_shrinkwrap_json(json_schema, config_file):
    """Check shrinkwrap file output"""
    result = main(
        lang="javascript",
        dep_file=Path("tests/data/example_npm_shrinkwrap.json"),
        deep_search=True,
        host=None,
        config=config_file
    )
    assert json_schema.is_valid(result)


# def test_package_lock_json(json_schema, config_file):
#     """Check package lock file output"""
#     result = main(
#         lang="javascript",
#         dep_file=Path("tests/data/example_package_lock.json"),
#         deep_search=True,
#         host=None,
#         config=config_file
#     )
#     assert result == ""
#     assert json_schema.is_valid(result)
#
#
# def test_yarn_v1_lock(json_schema, config_file):
#     """Check yarn.lock v1 file output"""
#     result = main(
#         lang="javascript",
#         dep_file=Path("tests/data/example_v1_yarn.lock"),
#         deep_search=True,
#         host=None,
#         config=config_file
#     )
#     assert result == ""
#     assert json_schema.is_valid(result)
#
#
# def test_yarn_v2_lock(json_schema, config_file):
#     """Check yarn.lock v2 file output"""
#     result = main(
#         lang="javascript",
#         dep_file=Path("tests/data/example_v2_yarn.lock"),
#         deep_search=True,
#         host=None,
#         config=config_file
#     )
#     assert result == ""
#     assert json_schema.is_valid(result)


def test_requirements_txt(json_schema, config_file):
    """Check requirements.txt file output"""
    result = main(
        lang="python",
        dep_file=Path("tests/data/example_requirements.txt"),
        deep_search=True,
        host=None,
        config=config_file
    )
    assert json_schema.is_valid(result)


def test_setup_py(json_schema, config_file):
    """Check setup.py file output"""
    result = main(
        lang="python",
        dep_file=Path("tests/data/example_setup.py"),
        deep_search=True,
        host=None,
        config=config_file
    )
    assert json_schema.is_valid(result)


def test_setup_cfg(json_schema, config_file):
    """Check setup.cfg file output"""
    result = main(
        lang="python",
        dep_file=Path("tests/data/example_setup.cfg"),
        deep_search=True,
        host=None,
        config=config_file
    )
    assert json_schema.is_valid(result)


def test_pyproject_toml(json_schema, config_file):
    """Check toml file output"""
    result = main(
        lang="python",
        dep_file=Path("tests/data/example_pyproject.toml"),
        deep_search=True,
        host=None,
        config=config_file
    )
    assert json_schema.is_valid(result)


def test_poetry_toml(json_schema, config_file):
    """Check poetry toml file output"""
    result = main(
        lang="python",
        dep_file=Path("tests/data/example_pyproject_poetry.toml"),
        deep_search=True,
        host=None,
        config=config_file
    )
    assert json_schema.is_valid(result)


def test_unsupported():
    """Check no extension output"""
    with pytest.raises(
            FileNotSupportedError,
            match="example_pipfile"
    ):
        result = main(
            lang="python",
            dep_file=Path("tests/data/example_pipfile"),
            deep_search=False,
            config=None
        )
        assert json_schema.is_valid(result)
