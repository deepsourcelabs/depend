"""Tests output obtained by parsing dependency files"""
import dependencies.py.py_worker


def test_requirements_txt():
    """Check requirements.txt file output"""
    with open("tests/data/example_requirements.txt") as f:
        txt_content = f.read()
    result = dependencies.py.py_worker.handle_requirements_txt(txt_content)
    assert result["dependencies"]
    

def test_setup_py():
    with open("tests/data/example_setup.py") as f:
        py_content = f.read()
    result = dependencies.py.py_worker.handle_setup_py(py_content)
    assert result["version"] == "1.55"


def test_setup_cfg():
    with open("tests/data/example_setup.cfg") as f:
        cfg_content = f.read()
    result = dependencies.py.py_worker.handle_setup_cfg(cfg_content)
    assert result["license"] == "MIT"


def test_pyproject_toml():
    with open("tests/data/example_pyproject.toml") as f:
        pyproject = f.read()
    result = dependencies.py.py_worker.handle_toml(pyproject)
    assert result


def test_poetry_toml():
    with open("tests/data/example_pyproject_poetry.toml") as f:
        pyproject = f.read()
    result = dependencies.py.py_worker.handle_toml(pyproject)
    assert result
