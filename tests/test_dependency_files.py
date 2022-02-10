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
