"""Test cli and overall pipeline for dependency-inspector"""
from pathlib import Path

from cli import main


def test_go_mod():
    """Check go.mod file output"""
    result = main(
        lang="go",
        dep_file=Path("tests/data/example_go.mod"),
        deep_search=False,
        config=None
    )
    assert result["pkg_dep"]


def test_package_json():
    """Check package.json file output"""
    result = main(
        lang="javascript",
        dep_file=Path("tests/data/example_package.json"),
        deep_search=False,
        config=None
    )
    assert result["pkg_dep"]


def test_npm_shrinkwrap_json():
    """Check shrinkwrap file output"""
    result = main(
        lang="javascript",
        dep_file=Path("tests/data/example_npm_shrinkwrap.json"),
        deep_search=False,
        config=None
    )
    assert result["pkg_dep"]


def test_package_lock_json():
    """Check package lock file output"""
    result = main(
        lang="javascript",
        dep_file=Path("tests/data/example_package_lock.json"),
        deep_search=False,
        config=None
    )
    assert result["pkg_dep"]


def test_yarn_v1_lock():
    """Check yarn.lock v1 file output"""
    result = main(
        lang="javascript",
        dep_file=Path("tests/data/example_v1_yarn.lock"),
        deep_search=False,
        config=None
    )
    assert result["pkg_dep"]


def test_yarn_v2_lock():
    """Check yarn.lock v2 file output"""
    result = main(
        lang="javascript",
        dep_file=Path("tests/data/example_v2_yarn.lock"),
        deep_search=False,
        config=None
    )
    assert result["pkg_dep"]


def test_requirements_txt():
    """Check requirements.txt file output"""
    result = main(
        lang="python",
        dep_file=Path("tests/data/example_requirements.txt"),
        deep_search=False,
        config=None
    )
    assert result["pkg_dep"]


def test_setup_py():
    """Check setup.py file output"""
    result = main(
        lang="python",
        dep_file=Path("tests/data/example_setup.py"),
        deep_search=False,
        config=None
    )
    assert result["pkg_dep"]


def test_setup_cfg():
    """Check setup.cfg file output"""
    result = main(
        lang="python",
        dep_file=Path("tests/data/example_setup.cfg"),
        deep_search=False,
        config=None
    )
    assert result["pkg_dep"]


def test_pyproject_toml():
    """Check toml file output"""
    result = main(
        lang="python",
        dep_file=Path("tests/data/example_pyproject.toml"),
        deep_search=False,
        config=None
    )
    assert result["pkg_lic"] == "BSD"


def test_poetry_toml():
    """Check poetry toml file output"""
    result = main(
        lang="python",
        dep_file=Path("tests/data/example_pyproject_poetry.toml"),
        deep_search=False,
        config=None
    )
    assert result["pkg_dep"]
