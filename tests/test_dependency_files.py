"""Tests output obtained by parsing dependency files"""
import dependencies.go.go_worker
import dependencies.js.js_worker


def test_go_mod():
    """Check go.mod file output"""
    with open("tests/data/example_go.mod") as f:
        mod_content = f.read()
    result = dependencies.go.go_worker.handle_go_mod(mod_content)
    assert result["Dep_ver"] == [
        'github.com/alecthomas/template;v0.0.0-20160405071501-a0175ee3bccc',
        'github.com/alecthomas/units;v0.0.0-20151022065526-2efee857e7cf',
        'github.com/gorilla/mux;v1.6.2',
        'github.com/sirupsen/logrus;v1.2.0',
        'gopkg.in/alecthomas/kingpin.v2;v2.2.6'
    ]


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
