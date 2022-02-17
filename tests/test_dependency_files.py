"""Tests output obtained by parsing dependency files"""
import dependencies.go.go_worker


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
