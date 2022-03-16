"""Tests output obtained by parsing dependency files"""
import dependencies.py.py_worker
import dependencies.js.js_worker


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


def test_package_json():
    """Check package.json file output"""
    with open("tests/data/example_package.json") as f:
        json_content = f.read()
    result = dependencies.js.js_worker.handle_json(json_content)
    assert result["version"] == "1.0.0"


def test_npm_shrinkwrap_json():
    """Check package.json file output"""
    with open("tests/data/example_npm_shrinkwrap.json") as f:
        json_content = f.read()
    result = dependencies.js.js_worker.handle_json(json_content)
    assert result["version"] == "0.0.1"


def test_package_lock_json():
    """Check package.json file output"""
    with open("tests/data/example_package_lock.json") as f:
        json_content = f.read()
    result = dependencies.js.js_worker.handle_json(json_content)
    assert result["version"] == "3.11.4"


def test_yarn_v1_lock():
    """Check yarn.lock v1 file output"""
    with open("tests/data/example_v1_yarn.lock") as f:
        yarn_content = f.read()
    result = dependencies.js.js_worker.handle_yarn_lock(yarn_content)
    assert result


def test_yarn_v2_lock():
    """Check yarn.lock v2 file output"""
    with open("tests/data/example_v2_yarn.lock") as f:
        yarn_content = f.read()
    result = dependencies.js.js_worker.handle_yarn_lock(yarn_content)
    assert result
