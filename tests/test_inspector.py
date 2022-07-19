"""Tests for all functions in inspector."""

from datetime import datetime

import pytest

import depend.inspector as inspector
from depend.dependencies.dep_types import Result
from depend.error import LanguageNotSupportedError, VCSNotSupportedError


@pytest.fixture
def dependency_payload():
    """
    Generates a fixed payload to test the script
    :return: List of dependencies with language as key
    """
    return {
        "javascript": ["react;0.12.0"],
        "python": ["pygithub"],
        "go": [
            "https://github.com/go-yaml/yaml;https://github.com/go-yaml/yaml",
            "github.com/cactus/go-statsd-client/v5/statsd",
        ],
    }


@pytest.fixture
def result_payload():
    """
    Generates a result object to test the script
    :return: Result object to manipulate
    """
    result: Result = {
        "import_name": "",
        "lang_ver": [],
        "pkg_name": "",
        "pkg_ver": "",
        "pkg_lic": ["Other"],
        "pkg_err": {},
        "pkg_dep": [],
        "timestamp": datetime.utcnow().isoformat(),
    }
    return result


def test_make_url_with_version():
    """Check if version specific url is generated for all languages"""
    assert (
        inspector.make_url("python", "aiohttp", "3.7.2")
        == "https://pypi.org/pypi/aiohttp/3.7.2/json"
    )
    assert (
        inspector.make_url("javascript", "diff", "5.0.0")
        == "https://registry.npmjs.org/diff/5.0.0"
    )
    assert (
        inspector.make_url("go", "bufio", "go1.17.6")
        == "https://pkg.go.dev/bufio@go1.17.6"
    )


def test_make_url_without_version():
    """Check if correct url is generated for all languages"""
    assert (
        inspector.make_url("python", "aiohttp") == "https://pypi.org/pypi/aiohttp/json"
    )
    assert inspector.make_url("javascript", "diff") == "https://registry.npmjs.org/diff"
    assert inspector.make_url("go", "bufio") == "https://pkg.go.dev/bufio"


def test_make_single_request_py():
    """Test version and license for python"""
    result, _ = inspector.make_single_request(
        "python", "aiohttp", "3.7.2", force_schema=False
    )
    assert result[0]["pkg_name"] == "aiohttp"
    assert result[0]["pkg_ver"] == "3.7.2"
    assert result[0]["pkg_lic"][0] == "Apache 2"
    assert len(result[0]["pkg_dep"]) != 0


def test_make_single_request_js():
    """Test version and license for javascript"""
    result, _ = inspector.make_single_request(
        "javascript", "react", "17.0.2", force_schema=False
    )
    assert result[0]["pkg_name"] == "react"
    assert result[0]["pkg_ver"] == "17.0.2"
    assert result[0]["pkg_lic"][0] == "MIT"
    assert len(result[0]["pkg_dep"]) != 0


def test_make_single_request_go():
    """Test version and license for go"""
    result, _ = inspector.make_single_request(
        "go",
        "github.com/getsentry/sentry-go",
        "v0.12.0",
        force_schema=False,
    )
    assert result[0]["pkg_name"] == "github.com/getsentry/sentry-go"
    assert result[0]["pkg_lic"][0] == "BSD-2-Clause"
    assert len(result[0]["pkg_dep"]) != 0


def test_make_single_request_go_redirect():
    """Test version and license for go on redirects"""
    result, _ = inspector.make_single_request(
        "go", "http", "go1.16.13", force_schema=False
    )
    assert result[0]["pkg_name"] == "http"
    assert result[0]["pkg_ver"] == "go1.16.13"
    assert result[0]["pkg_lic"][0] == "BSD-3-Clause"


def test_make_single_request_go_github():
    """Test version and license for go GitHub fallthrough"""
    result, _ = inspector.make_single_request(
        "go", "gopkg.in/yaml.v3", "https://github.com/go-yaml/yaml", force_schema=False
    )
    assert result[0]["pkg_lic"][0] == "Apache Software License"
    assert len(result[0]["pkg_dep"]) != 0


def test_make_single_request_rust():
    """Test version and license for javascript"""
    result, _ = inspector.make_single_request("rust", "reqrnpdno", force_schema=False)
    assert result[0]["pkg_dep"]


def test_make_single_request_rust_ver():
    """Test version and license for javascript"""
    result, _ = inspector.make_single_request(
        "rust", "picnic-sys", "3.0.14", force_schema=False
    )
    assert result[0]["pkg_dep"]


def test_make_single_request_rust_git():
    """Test version and license for javascript"""
    result, _ = inspector.make_single_request(
        "rust",
        "sciter-rs",
        "https://github.com/open-trade/rust-sciter||dyn",
        force_schema=False,
    )
    assert result[0]["pkg_dep"]


def test_make_multiple_requests(dependency_payload):
    """Multiple package requests for JavaScript NPM and Go"""
    result = [
        inspector.make_multiple_requests(lang, dependencies, 1)
        for lang, dependencies in dependency_payload.items()
    ]
    assert len(result) == 3


def test_make_vcs_request(result_payload):
    """Test VCS handler"""
    inspector.handle_vcs("go", "github.com/getsentry/sentry-go", result_payload)
    assert result_payload["pkg_lic"] == ['BSD 2-Clause "Simplified" License']


def test_unsupported_language_fails():
    """Checks if exception is raised for unsupported language"""
    with pytest.raises(LanguageNotSupportedError, match="bhailang"):
        inspector.make_url("bhailang", "foo")


def test_unsupported_vcs_fails(result_payload):
    """Checks if exception is raised for unsupported pattern"""
    with pytest.raises(VCSNotSupportedError, match="gitlab"):
        inspector.handle_vcs("go", "gitlab.com/secmask/awserver", result_payload)


def test_make_single_request_cs():
    """Test version and license for c#"""
    result, _ = inspector.make_single_request(
        "cs", "Microsoft.Bcl.AsyncInterfaces", force_schema=False
    )
    assert result


def test_make_single_request_cs_ver():
    """Test version and license for c#"""
    result, _ = inspector.make_single_request(
        "cs",
        "Walter.Web.Firewall.Core.3.x",
        "2020.8.25.1",
        force_schema=False,
    )
    assert result


def test_make_single_request_php():
    """Test version and license for php"""
    result, _ = inspector.make_single_request(
        "php", "folospace/socketio", force_schema=False
    )
    assert result[0]["pkg_dep"]


def test_make_single_request_php_ver():
    """Test version and license for php"""
    result, _ = inspector.make_single_request(
        "php", "ajgarlag/psr15-dispatcher", "0.4.1", force_schema=False
    )
    assert result[0]["pkg_dep"]
