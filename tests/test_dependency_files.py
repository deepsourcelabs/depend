"""Tests output obtained by parsing dependency files"""
import helper


def test_go_mod():
    """Check .mod file output"""
    with open("tests/data/example.mod") as f:
        mod_content = f.read()
    result = helper.handle_go_mod(mod_content)
    assert result["Dep_ver"]
