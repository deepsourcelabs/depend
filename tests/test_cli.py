"""Test cli and overall pipeline for murdock"""
import pytest
from jsonschema import validate

from depend.cli import main


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
                                            "import_name": {"type": "string"},
                                            "lang_ver": {
                                                "type": "array",
                                                "items": {"type": "string"},
                                            },
                                            "pkg_lic": {
                                                "type": "array",
                                                "items": {"type": "string"},
                                            },
                                            "pkg_err": {"type": "object"},
                                            "pkg_dep": {
                                                "type": "array",
                                                "items": {"type": "string"},
                                            },
                                            "timestamp": {"type": "string"},
                                        },
                                        "additionalProperties": False,
                                    }
                                },
                            },
                        },
                        "required": ["versions"],
                    },
                    "additionalProperties": False,
                },
                "additionalProperties": False,
            },
        }
        validate(instance=json_list, schema=j_schema)
        return True


@pytest.fixture
def json_schema():
    """Schema helper functions"""
    return Helpers


def test_cs(json_schema):
    """C# fetching test"""
    result = main(
        lang="cs",
        packages="System.IO;4.3.0",
        dep_file=None,
        depth=None,
    )
    assert json_schema.is_valid(result)
    assert {key for res_obj in result for key in res_obj} == {
        "Microsoft.NETCore.Platforms",
        "System.Runtime",
        "System.IO",
        "Microsoft.NETCore.Targets",
        "System.Text.Encoding",
        "System.Threading.Tasks",
    }


def test_go(json_schema):
    """Go fetching test"""
    result = main(
        lang="go",
        packages="reflectlite;go1.18.4",
        dep_file=None,
        depth=None,
    )
    assert json_schema.is_valid(result)
    assert {key for res_obj in result for key in res_obj} == {
        "abi",
        "math",
        "cpu",
        "goarch",
        "atomic",
        "reflectlite",
        "unsafeheader",
        "sys",
        "goexperiment",
        "runtime",
        "goos",
        "unsafe",
        "bytealg",
        "syscall",
    }


def test_js(json_schema):
    """JavaScript fetching test"""
    result = main(
        lang="javascript",
        packages="uri-js;<=4.4.1,ajv;8.11.0",
        dep_file=None,
        depth=None,
    )
    assert json_schema.is_valid(result)
    assert {key for res_obj in result for key in res_obj} == {
        "json-schema-traverse",
        "uri-js",
        "require-from-string",
        "punycode",
        "fast-deep-equal",
        "ajv",
    }


def test_php(json_schema):
    """PHP fetching test"""
    result = main(
        lang="php",
        packages="nunomaduro/collision;^6.0",
        dep_file=None,
        depth=None,
    )
    assert json_schema.is_valid(result)
    assert {key for res_obj in result for key in res_obj} == {
        "symfony/polyfill-ctype",
        "symfony/service-contracts",
        "psr/log",
        "symfony/polyfill-intl-normalizer",
        "psr/container",
        "symfony/console",
        "nunomaduro/collision",
        "facade/ignition-contracts",
        "symfony/string",
        "symfony/polyfill-mbstring",
        "filp/whoops",
        "symfony/polyfill-intl-grapheme",
        "symfony/deprecation-contracts",
    }


def test_python(json_schema):
    """Python fetching test"""
    result = main(
        lang="python",
        packages="pygit2;==1.9.2",
        dep_file=None,
        depth=None,
    )
    assert json_schema.is_valid(result)
    assert {key for res_obj in result for key in res_obj} == {
        "cached-property",
        "pycparser",
        "pygit2",
        "cffi",
    }


def test_rust(json_schema):
    """Rust fetching test"""
    result = main(
        lang="rust",
        packages="libc;0.2.126",
        dep_file=None,
        depth=None,
    )
    assert json_schema.is_valid(result)
    assert {key for res_obj in result for key in res_obj} == {
        "rustc-std-workspace-core",
        "libc",
    }
