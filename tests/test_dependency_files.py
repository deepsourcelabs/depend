"""Tests output obtained by parsing dependency files"""
import helper


def test_go_mod():
    """Check go.mod file output"""
    with open("tests/data/example_go.mod") as f:
        mod_content = f.read()
    result = helper.handle_go_mod(mod_content)
    assert result["Dep_ver"]


def test_requirements_txt():
    """Check requirements.txt file output"""
    with open("tests/data/example_requirements.txt") as f:
        txt_content = f.read()
    result = helper.handle_requirements_txt(txt_content)
    assert len(result) == 20


def test_package_json():
    """Check package.json file output"""
    with open("tests/data/example_package.json") as f:
        json_content = f.read()
    result = helper.handle_package_json(json_content)
    assert result["version"] == "1.0.0"


def test_yarn_v1_lock():
    """Check yarn.lock v1 file output"""
    with open("tests/data/example_v1_yarn.lock") as f:
        yarn_content = f.read()
    result = helper.handle_yarn_lock(yarn_content)
    assert result


def test_yarn_v2_lock():
    """Check yarn.lock v2 file output"""
    with open("tests/data/example_v2_yarn.lock") as f:
        yarn_content = f.read()
    result = helper.handle_yarn_lock(yarn_content)
    assert result


def test_setup_py():
    with open("tests/data/example_setup.py") as f:
        py_content = f.read()
    result = helper.handle_setup_py(py_content)
    assert result
