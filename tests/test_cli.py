"""Test cli and overall pipeline for dependency-inspector"""
from pathlib import Path
from schema import Schema, Or, Optional
import pytest

from cli import main
from error import FileNotSupportedError


@pytest.fixture
def json_schema():
    """Sets up schema check"""
    schema = Schema({
        "lang_ver": str,
        "pkg_name": str,
        "pkg_ver": str,
        "pkg_lic": str,
        "pkg_err": str,
        "pkg_dep": Or(list, str),
    })
    return schema


def test_go_mod(json_schema):
    """Check go.mod file output"""
    result = main(
        lang="go",
        dep_file=Path("tests/data/example_go.mod"),
        deep_search=False,
        config=None
    )
    assert json_schema.is_valid(result)


def test_package_json(json_schema):
    """Check package.json file output"""
    result = main(
        lang="javascript",
        dep_file=Path("tests/data/example_package.json"),
        deep_search=False,
        config=None
    )
    assert json_schema.is_valid(result)


def test_npm_shrinkwrap_json(json_schema):
    """Check shrinkwrap file output"""
    result = main(
        lang="javascript",
        dep_file=Path("tests/data/example_npm_shrinkwrap.json"),
        deep_search=False,
        config=None
    )
    assert json_schema.is_valid(result)


def test_package_lock_json(json_schema):
    """Check package lock file output"""
    result = main(
        lang="javascript",
        dep_file=Path("tests/data/example_package_lock.json"),
        deep_search=False,
        config=None
    )
    assert json_schema.is_valid(result)


def test_yarn_v1_lock(json_schema):
    """Check yarn.lock v1 file output"""
    result = main(
        lang="javascript",
        dep_file=Path("tests/data/example_v1_yarn.lock"),
        deep_search=False,
        config=None
    )
    assert json_schema.is_valid(result)


def test_yarn_v2_lock(json_schema):
    """Check yarn.lock v2 file output"""
    result = main(
        lang="javascript",
        dep_file=Path("tests/data/example_v2_yarn.lock"),
        deep_search=False,
        config=None
    )
    assert json_schema.is_valid(result)


def test_requirements_txt(json_schema):
    """Check requirements.txt file output"""
    result = main(
        lang="python",
        dep_file=Path("tests/data/example_requirements.txt"),
        deep_search=False,
        config=None
    )
    assert json_schema.is_valid(result)


def test_setup_py(json_schema):
    """Check setup.py file output"""
    result = main(
        lang="python",
        dep_file=Path("tests/data/example_setup.py"),
        deep_search=False,
        config=None
    )
    assert json_schema.is_valid(result)


def test_setup_cfg(json_schema):
    """Check setup.cfg file output"""
    result = main(
        lang="python",
        dep_file=Path("tests/data/example_setup.cfg"),
        deep_search=False,
        config=None
    )
    assert json_schema.is_valid(result)


def test_pyproject_toml(json_schema):
    """Check toml file output"""
    result = main(
        lang="python",
        dep_file=Path("tests/data/example_pyproject.toml"),
        deep_search=False,
        config=None
    )
    assert json_schema.is_valid(result)


def test_poetry_toml(json_schema):
    """Check poetry toml file output"""
    result = main(
        lang="python",
        dep_file=Path("tests/data/example_pyproject_poetry.toml"),
        deep_search=False,
        config=None
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

